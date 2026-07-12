"""初期ヒアリング回答中の「AIに補足する」チャット。

回答提出前に呼ばれるため BigQuery には一切触れず、会話の材料
（質問文・入力中の回答・これまでの補足チャット）はすべてリクエストで受け取り、
エージェント（Gemini）に1往復だけ問い合わせる。補足内容そのものの保存は
従来通り提出時の chat_messages / chat_transcript が担う。

出力は2モードをサーバ側で制御する:
- followup: 補足を受け止めて深掘り質問を最大1つ返す（通常時）
- summary : ユーザー送信が3の倍数回に達したら、回答欄にそのまま貼れる
            まとめ文章を返す（フロントの「回答欄に反映する」ボタンの材料）

モデルには応答の1行目を必ず「FOLLOWUP:」または「SUMMARY:」で始めさせ、
サーバがマーカーを解析・除去してモードを確定する（Stage1 の
ONBOARDING_STAGE1_COMPLETE と同じマーカー方式）。マーカーが欠けたり
指示と食い違う場合は安全側（followup 扱い）に倒す。
"""
from __future__ import annotations

import re
from typing import Literal

from app.schemas.survey import IntakeAssistRequest, IntakeAssistResponse
from app.services import agent_client

# エージェント不達・クラッシュ時もチャットUXを壊さないための応答。
# copilot_service と同じ思想（エラーをそのまま見せない）。
_FALLBACK_REPLY = (
    "すみません、いまうまく応答できませんでした。"
    "差し支えなければ、具体的な出来事や例をそのまま回答欄に書き足していただければ大丈夫です。"
)

# 1往復の会話なので copilot(300s) より短めに切り上げる
_TIMEOUT_SECONDS = 90.0

# ユーザー送信が何回目ごとにまとめモードへ切り替えるか
_SUMMARY_EVERY_N_USER_MESSAGES = 3

# 全角/半角コロン・前後空白に耐性を持たせたマーカー解析
_MARKER_RE = re.compile(r'^\s*(FOLLOWUP|SUMMARY)\s*[:：]\s*', re.IGNORECASE)


def _common_context(company_id: str, data: IntakeAssistRequest) -> str:
    history_lines = [
        f"- {'AI' if m.role == 'assistant' else '回答者'}: {m.text}" for m in data.chat_history
    ] or ["- （まだありません）"]
    return f"""あなたは中小企業の経営者・現場担当者への初期ヒアリング(企業ID: {company_id})を補助するアシスタントです。回答者はいま、アンケートの1問に回答している途中で、補足を伝えるためにチャットを開いています。

## 現在の質問
{data.question_text}

## この質問の狙い
{data.purpose or '（指定なし）'}

## 回答欄に入力中の内容
{data.current_answer or '（まだ入力されていません）'}

## これまでの補足チャット
{chr(10).join(history_lines)}

## 回答者からの新しい補足
{data.user_message}"""


def _build_followup_prompt(company_id: str, data: IntakeAssistRequest) -> str:
    return f"""{_common_context(company_id, data)}

## 応答ルール（厳守）
- ツールは一切呼び出さず、会話の返信テキストだけを出力する。
- 応答の1行目は必ず「FOLLOWUP:」で始め、その直後に返信本文を続ける。
- 質問の狙いに照らして情報が不足している場合のみ、深掘り質問を1つだけする。補足内容に触れる場合も、事実の確認だけを簡潔に書く。
- まとめや要約の出力はこのターンでは禁止。
- 淡々とした丁寧な文体にする。「なるほど」「素晴らしいですね」「いいですね」のような相槌・感嘆・評価の表現、および感嘆符（!・！）は使わない。
- 回答者はITや経営の専門知識を持たない。「原価管理」「KPI」「指標」「データ基盤」「システム」のような業務・IT用語は使わず、日常の実感や具体的なエピソードを尋ねる平易な言葉にする。
- 質問は1つのことだけを聞き、回答者が1分以内に答えられる長さにする。
- 全体で200字以内。Markdownの見出しやリストは使わず、話し言葉の文章で返す。"""


def _build_summary_prompt(company_id: str, data: IntakeAssistRequest) -> str:
    return f"""{_common_context(company_id, data)}

## 応答ルール（厳守）
- ツールは一切呼び出さず、テキストだけを出力する。
- 応答の1行目は必ず「SUMMARY:」で始め、その直後にまとめ文章を続ける。
- まとめ文章は「回答欄に入力中の内容」と「補足チャットで回答者が話した内容」をすべて統合し、アンケートの回答欄にそのまま貼れる文章にする。
- 回答者本人が書いたような一人称の自然な文体にする（「〜です」「〜しています」）。
- 前置き・後置き・見出し・箇条書きは禁止。まとめ文章そのものだけを出力する。
- 深掘り質問はこのターンでは禁止。
- 感嘆・評価の表現や感嘆符（!・！）は使わず、事実を淡々と述べる文体にする。
- 100〜300字程度に収める。回答者が話していないことを推測で足さない。"""


def _is_summary_turn(data: IntakeAssistRequest) -> bool:
    """今回のユーザー送信を含めた通算送信回数が3の倍数ならまとめモード。"""
    user_message_count = sum(1 for m in data.chat_history if m.role == 'user') + 1
    return user_message_count % _SUMMARY_EVERY_N_USER_MESSAGES == 0


def _parse_reply(raw_reply: str, expected_summary: bool) -> tuple[Literal['followup', 'summary'], str, str | None]:
    """マーカーを解析して (mode, reply, answer_draft) を返す。

    モデルがマーカーを守らなかった場合は安全側に倒す:
    まとめ期待でマーカー無し/不一致なら followup 扱い（誤った本文を
    ワンタップで回答欄に書き込ませない）。"""
    match = _MARKER_RE.match(raw_reply)
    body = _MARKER_RE.sub('', raw_reply, count=1).strip()
    marker = match.group(1).upper() if match else None
    if expected_summary and marker == 'SUMMARY' and body:
        return 'summary', body, body
    return 'followup', body or raw_reply.strip(), None


class IntakeAssistService:
    async def assist(self, company_id: str, data: IntakeAssistRequest) -> IntakeAssistResponse:
        summary_turn = _is_summary_turn(data)
        prompt = (
            _build_summary_prompt(company_id, data)
            if summary_turn
            else _build_followup_prompt(company_id, data)
        )
        # 質問ごとにセッションを分け、同じ質問での連続やりとりは
        # エージェント側の会話文脈にも乗るようにする
        session_id = f"intake_assist_{company_id}_{data.question_id}"
        try:
            raw_reply = await agent_client.run_agent_turn(
                user_id=company_id,
                session_id=session_id,
                message=prompt,
                timeout_seconds=_TIMEOUT_SECONDS,
            )
        except Exception:
            raw_reply = ""
        if not raw_reply.strip():
            return IntakeAssistResponse(
                company_id=company_id, question_id=data.question_id, reply=_FALLBACK_REPLY,
            )
        mode, reply, answer_draft = _parse_reply(raw_reply, expected_summary=summary_turn)
        return IntakeAssistResponse(
            company_id=company_id,
            question_id=data.question_id,
            reply=reply,
            mode=mode,
            answer_draft=answer_draft,
        )


intake_assist_service = IntakeAssistService()
