from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timezone

from fastapi import BackgroundTasks
from google.api_core.exceptions import NotFound

from app.core.config import settings
from app.crud.bigquery_crud import bigquery_crud
from app.crud.storage_crud import storage_crud
from app.schemas.company import CompanyOnboardingPrepareRequest, CompanyOnboardingPrepareResponse
from app.schemas.survey import SurveyAnswerCreate
from app.services import agent_client
from app.services.bigquery_service import bigquery_service
from app.services.company_service import company_service
from app.services.research_service import research_service
from app.services.survey_service import survey_service
from app.services.wiki_service import wiki_service
from app.utils.bigquery_sql import sql_literal


def _wiki_written_since(company_id: str, since_epoch: float) -> bool:
    """The agent's self-reported completion text is not trustworthy on its
    own: observed directly against real Vertex AI Gemini, it can (a) report
    ONBOARDING_FAILED over one transient hiccup (e.g. a BigQuery
    streaming-insert 404 on a table created moments earlier) even though it
    went on to finish everything else, and worse, (b) report success while
    having only *described* a plausible-looking write_wiki_files result in
    prose without actually calling the tool. Wiki files actually existing in
    storage is the pipeline's last step and the one directly verifiable side
    effect, so it — not the model's text — is the authority on completion.

    Existence alone isn't enough, though: a company re-running onboarding
    (e.g. a retry, or answers submitted again) already has wiki files from
    its *previous* run sitting under the same prefix, so a plain existence
    check reports success even when this run's agent chain crashed before
    ever reaching write_wiki_files. Requiring a file updated at/after this
    run's start closes that gap."""
    for item in storage_crud.list_prefix(f'tenants/{company_id}/wiki/current/'):
        updated = item.get('updated')
        if updated is None:
            continue
        updated_epoch = float(updated) if isinstance(updated, (int, float)) else datetime.fromisoformat(updated).timestamp()
        if updated_epoch >= since_epoch:
            return True
    return False


def _onboarding_followup_count_since(company_id: str, since_epoch: float) -> int:
    """How many origin="onboarding" follow-up questions this stage-1 run has
    generated so far — the stage-1 success signal, mirroring how
    _wiki_written_since is stage-2's. Scoped to since_epoch for the same
    reason: a retried run must not count questions a previous attempt
    already registered."""
    if settings.dry_run:
        return 0
    since_iso = datetime.fromtimestamp(since_epoch, tz=timezone.utc).isoformat()
    table = settings.qualified_table(company_id, 'research_followup_question_events')
    sql = f"""
SELECT COUNT(*) AS c FROM `{table}`
WHERE origin = 'onboarding' AND generated_at >= TIMESTAMP({sql_literal(since_iso)})
""".strip()
    try:
        rows = bigquery_crud.query_rows(sql)
    except NotFound:
        return 0
    return int(rows[0]['c']) if rows else 0


def _has_any_onboarding_followups(company_id: str) -> bool:
    """Whether stage 1 ever generated onboarding follow-up questions for
    this company, regardless of when. Used to tell apart a stage-1 failure
    (no follow-ups were ever generated) from a stage-2 failure (follow-ups
    exist and were already answered) when retrying a failed run."""
    if settings.dry_run:
        return False
    table = settings.qualified_table(company_id, 'research_followup_question_events')
    sql = f"SELECT 1 FROM `{table}` WHERE origin = 'onboarding' LIMIT 1"
    try:
        return bool(bigquery_crud.query_rows(sql))
    except NotFound:
        return False


def _onboarding_followup_qa(company_id: str) -> list[dict]:
    """Question/answer pairs from this company's onboarding follow-up round,
    for folding into the stage-2 (finalize) prompt."""
    if settings.dry_run:
        return []
    questions_table = settings.qualified_table(company_id, 'research_followup_question_events')
    answers_table = settings.qualified_table(company_id, 'followup_answer_events')
    sql = f"""
SELECT q.question_text AS question_text, a.answer_text AS answer_text, a.respondent_role AS respondent_role
FROM `{questions_table}` q
JOIN `{answers_table}` a ON a.followup_question_id = q.followup_question_id
WHERE q.company_id = {sql_literal(company_id)} AND q.origin = 'onboarding'
""".strip()
    try:
        return bigquery_crud.query_rows(sql)
    except NotFound:
        return []


def _chat_supplement(answer_json: dict | str | None) -> str | None:
    """「AIに補足する」チャットで回答者が入力した補足テキストを1本にまとめる。
    answer_json は BigQuery 経由だと JSON 文字列で来ることがあるため両対応。"""
    if isinstance(answer_json, str):
        try:
            answer_json = json.loads(answer_json)
        except ValueError:
            return None
    messages = (answer_json or {}).get('chat_messages') or []
    user_texts = [
        m.get('text', '').strip()
        for m in messages
        if isinstance(m, dict) and m.get('role') == 'user' and m.get('text', '').strip()
    ]
    return ' / '.join(user_texts) or None


def _answers_payload(answers: list[SurveyAnswerCreate]) -> list[dict]:
    return [
        {
            "question_id": a.question_id,
            "question_text": a.question_text,
            "respondent_role": a.respondent_role,
            "raw_answer": a.raw_answer,
            "numeric_value": a.numeric_value,
            "response_id": a.response_id,
            # 回答中の「AIに補足する」チャットで得た追加情報。raw_answer と
            # 併せて KPI 候補・グラフ・追加質問の分析材料にする
            "supplement": _chat_supplement(a.answer_json),
        }
        for a in answers
    ]


def _build_stage1_message(company_id: str, company_name: str, answers_payload: list[dict]) -> str:
    return f"""企業ID: {company_id}
企業名: {company_name}

以下は初期アンケート(18問)の回答です。各回答の supplement は、回答者が「AIに補足する」チャットで追加入力した補足情報です(nullの場合は補足なし)。raw_answer と併せて分析に使ってください。この内容をもとに、この企業のオンボーディング処理の第一段階を実行してください。

{json.dumps(answers_payload, ensure_ascii=False, indent=2)}

実行してほしい手順:
1. ensure_shared_dataset と create_core_tables(company_id="{company_id}") で、この企業用のBigQuery基本テーブル(survey_responses/knowledge_nodes/knowledge_edges)とプロパティグラフを作成する。
2. create_tenant_tables(company_id="{company_id}") で、KPI候補・重点管理指標候補などのテナント用テーブルを作成する。
3. insert_onboarding_answer_events は、上記の回答すべてを1つの records 配列にまとめて1回だけ呼び出す(回答1件ごとに個別に呼び出さないこと)。
4. 上記の回答内容を分析し、KPI候補・重点管理指標候補を抽出して insert_kpi_candidates / insert_focus_metric_candidates で登録する。
5. 上記の回答内容から企業構造のナレッジグラフを抽出し、upsert_knowledge_nodes / upsert_knowledge_edges で保存する。先に list_knowledge_nodes(company_id="{company_id}") で既存ノードを確認し、同じ実体を指すノードがあれば新規作成せずその node_id を使うこと。各ノード・エッジの source_response_id には、根拠となった回答の response_id(上記JSONに含まれる)を設定すること。node_type と edge_type は指示済みの正式語彙のみを使うこと。
6. 上記の回答内容から、この企業についてさらに深掘りすべき固有の追加質問を2〜5件考え、insert_research_followup_question_events で登録する。各質問の origin は必ず "onboarding" にすること(これは継続的な収集用の定期質問ではなく、Wikiを確定する前に一度だけ回答してもらう質問です)。

   質問文の書き方(重要): 回答者はITや経営の専門知識を持たない事業主・現場担当者です。
   「原価管理」「データ基盤」「システム」「KPI」「指標」のような業務・IT用語を使った
   質問は絶対に避け、初期アンケートの質問(例:「顧客が御社を選ぶ一番の理由は何だと思いますか？」)
   と同じように、日常の実感・具体的なエピソードを尋ねる平易な言葉にすること。狙いは同じ情報を
   引き出すことでも、聞き方はやさしくする。
   - 悪い例:「商品別の原価や売上はどのように管理されていますか？商品別利益を把握するために、
     どのようなデータやシステムが不足しているとお考えですか？」
   - 良い例:「扱っている商品の中で、『これは実はあまり儲かっていないかも』と感じるものは
     ありますか？それはなぜそう感じますか？」
   1問につき1つのことだけを聞き、回答者が1分程度で答えられる長さにすること。

7. 上記の内容をもとに render_wiki_files(status="draft") でWikiドラフトの各ファイルを生成し、write_wiki_files で保存する。

途中のツール呼び出しが失敗しても構わないので、必ず最後まで進めてください。手順5〜7は
実際にツールを呼び出して結果を確認すること — ツールを呼ばずに成功したかのような結果を文章で
捏造してはいけません。最後の返信の1行目は、全ての手順が完了した場合は必ず
「ONBOARDING_STAGE1_COMPLETE」、途中で続行できない手順がある場合は
「ONBOARDING_FAILED: <理由>」のどちらか一方だけを出力し、その後に実行結果の要約を続けてください。"""


def _build_stage2_message(
    company_id: str, company_name: str, answers_payload: list[dict], followup_qa: list[dict]
) -> str:
    return f"""企業ID: {company_id}
企業名: {company_name}

以下は初期アンケート(18問)の回答と、その後に実施した追加質問への回答です。この内容をもとに、この企業のオンボーディング処理の最終段階(Wikiの確定と継続調査の設定)を実行してください。

## 初期アンケート回答
{json.dumps(answers_payload, ensure_ascii=False, indent=2)}

## 追加質問への回答
{json.dumps(followup_qa, ensure_ascii=False, indent=2)}

実行してほしい手順:
1. 上記すべての回答を踏まえて、KPI候補・重点管理指標候補を見直し、必要であれば insert_kpi_candidates / insert_focus_metric_candidates で追加・更新登録する。
2. 上記すべての回答(追加質問への回答を含む)を踏まえてナレッジグラフを見直し、upsert_knowledge_nodes / upsert_knowledge_edges で追加・更新する。先に list_knowledge_nodes(company_id="{company_id}") で既存ノードを確認し、同じ実体を指すノードがあれば新規作成せずその node_id を使うこと。初期アンケート回答由来のノード・エッジには source_response_id(上記JSONの response_id)を設定すること。node_type と edge_type は指示済みの正式語彙のみを使うこと。
3. 継続的な収集が必要な指標があれば、create_research_collection_table と register_research_schedule_item で収集用テーブルと収集スケジュールを用意する。
4. 上記の内容をもとに render_wiki_files(status="confirmed") でWikiの各ファイルを再生成し、write_wiki_files で保存して確定する。

途中のツール呼び出しが失敗しても構わないので、必ず最後まで進めてください。write_wiki_files は
実際に呼び出して結果を確認すること — ツールを呼ばずに成功したかのような結果を文章で捏造しては
いけません。最後の返信の1行目は、全ての手順が完了した場合は必ず「ONBOARDING_COMPLETE」、途中で
続行できない手順がある場合は「ONBOARDING_FAILED: <理由>」のどちらか一方だけを出力し、その後に
実行結果の要約を続けてください。"""


# The multi-step tool chain this triggers (table DDL -> tenant tables ->
# KPI/focus-metric extraction -> wiki generation) occasionally makes the model
# emit a malformed function call partway through and crash the run (observed
# directly, repeatedly, against real Vertex AI Gemini — most often right as
# knowledge_agent takes over after the orchestrator's handoff). This is a
# real model-reliability limitation with this many tools/complex schemas, not
# something back-end retry logic can fully paper over; 3 attempts trades a
# meaningfully better success rate for proportionally higher LLM cost. A
# retry uses a fresh session so the model starts the chain over; the
# table-creation/write tools it re-runs are idempotent (CREATE TABLE IF NOT
# EXISTS, MERGE-based upserts), except onboarding_answer_events, which may
# get a harmless duplicate append row on retry.
_MAX_ATTEMPTS = 3


class OnboardingService:
    def prepare(self, company_id: str, data: CompanyOnboardingPrepareRequest) -> CompanyOnboardingPrepareResponse:
        initial_survey = survey_service.generate_common_initial_survey(company_id)
        ddl = bigquery_service.generate_core_tables_ddl(company_id)
        wiki_markdown, wiki_json = wiki_service.render_initial_wiki(company_id, data.company_name, initial_survey)
        if data.industry_hint:
            wiki_json['industry_hint'] = data.industry_hint
        if data.size_hint:
            wiki_json['size_hint'] = data.size_hint
        return CompanyOnboardingPrepareResponse(company_id=company_id, company_name=data.company_name, dataset_id=settings.dataset_id(), core_tables_ddl=ddl.ddl, initial_survey=initial_survey, wiki_markdown=wiki_markdown, wiki_json=wiki_json)

    async def run_agent_onboarding(self, company_id: str, answers: list[SurveyAnswerCreate]) -> None:
        """Kick off stage 1 of the real ADK agent pipeline (BigQuery table
        creation, KPI/focus-metric extraction, onboarding follow-up question
        generation, draft wiki) once a company finishes its initial intake.
        Invoked as a FastAPI background task from
        survey.create_initial_survey_submission — the agent run itself can
        take minutes, so this must never block the HTTP response.

        Ends in onboarding_status='awaiting_followup' (the normal case: the
        agent generated follow-up questions and now waits on
        maybe_finalize_after_followup to trigger stage 2), or 'completed'
        directly if the agent decided no follow-up was needed and wrote the
        full wiki in this same run, or 'failed'.
        """
        company = company_service.get(company_id)
        if company is not None and company.get('onboarding_status') == 'processing':
            return
        company_name = company['company_name'] if company else company_id
        company_service.update_onboarding_status(company_id, 'processing')
        message = _build_stage1_message(company_id, company_name, _answers_payload(answers))
        started_at = time.time()

        last_error: Exception | None = None
        for attempt in range(_MAX_ATTEMPTS):
            reply = ''
            try:
                reply = await agent_client.run_agent_turn(
                    user_id=company_id, session_id=f'onboarding_stage1_{company_id}_{attempt}', message=message
                )
                last_error = None
            except Exception as exc:
                last_error = exc
            # Checked unconditionally, whether or not the HTTP call above
            # raised, since the tools can have run for real server-side even
            # if the response itself failed to parse.
            if _onboarding_followup_count_since(company_id, started_at) > 0:
                research_service.tick(company_id)
                company_service.update_onboarding_status(company_id, 'awaiting_followup')
                return
            if _wiki_written_since(company_id, started_at):
                # Agent judged no follow-up was needed and went straight to
                # a full wiki write this run — the user explicitly allowed
                # for this ordering, so treat it as fully complete.
                company_service.update_onboarding_status(company_id, 'completed')
                return
            if last_error is None:
                last_error = RuntimeError(
                    f'agent run finished without generating follow-up questions or a wiki: {reply[:500]}'
                )
            if attempt < _MAX_ATTEMPTS - 1:
                await asyncio.sleep(1.0)

        company_service.update_onboarding_status(company_id, 'failed', str(last_error)[:1000])

    async def finalize_onboarding(self, company_id: str) -> None:
        """Stage 2: fired once every onboarding-origin follow-up question has
        been answered (see maybe_finalize_after_followup). Re-renders and
        confirms the wiki using the original answers plus the follow-up
        answers, and sets up the recurring research schedule."""
        company = company_service.get(company_id)
        company_name = company['company_name'] if company else company_id
        company_service.update_onboarding_status(company_id, 'finalizing')
        answers_payload = [
            {
                "question_id": a.question_id,
                "question_text": a.question_text,
                "respondent_role": a.respondent_role,
                "raw_answer": a.raw_answer,
                "numeric_value": a.numeric_value,
                "response_id": a.response_id,
                "supplement": _chat_supplement(a.answer_json),
            }
            for a in survey_service.get_initial_survey_status(company_id).answers
        ]
        followup_qa = _onboarding_followup_qa(company_id)
        message = _build_stage2_message(company_id, company_name, answers_payload, followup_qa)
        started_at = time.time()

        last_error: Exception | None = None
        for attempt in range(_MAX_ATTEMPTS):
            reply = ''
            try:
                reply = await agent_client.run_agent_turn(
                    user_id=company_id, session_id=f'onboarding_stage2_{company_id}_{attempt}', message=message
                )
                last_error = None
            except Exception as exc:
                last_error = exc
            if _wiki_written_since(company_id, started_at):
                company_service.update_onboarding_status(company_id, 'completed')
                return
            if last_error is None:
                last_error = RuntimeError(f'finalize run finished without writing wiki files: {reply[:500]}')
            if attempt < _MAX_ATTEMPTS - 1:
                await asyncio.sleep(1.0)

        company_service.update_onboarding_status(company_id, 'failed', str(last_error)[:1000])

    def maybe_finalize_after_followup(self, company_id: str, background_tasks: BackgroundTasks) -> None:
        """Called from research.py's submit_followup_answer after each
        answer is recorded. Once no onboarding-origin follow-up assignment
        is left open, moves the company straight to stage 2 — finalization
        is automatic, with no separate "confirm" action for the user."""
        company = company_service.get(company_id)
        if company is None or company.get('onboarding_status') != 'awaiting_followup':
            return
        open_followups = research_service.list_assignments(company_id, status='open', origin='onboarding')
        if open_followups.items:
            return
        company_service.update_onboarding_status(company_id, 'finalizing')
        background_tasks.add_task(self.finalize_onboarding, company_id)

    async def retry_failed_onboarding(self, company_id: str) -> None:
        """Manually re-run whichever stage actually failed (e.g. the agent
        server was briefly unreachable — 'All connection attempts failed' —
        during stage 2), without making the user redo any answers. Whether
        onboarding-origin follow-up questions already exist tells stage-1
        failures (none generated yet) apart from stage-2 failures (they
        exist and were already answered)."""
        company = company_service.get(company_id)
        if company is None or company.get('onboarding_status') != 'failed':
            return
        if _has_any_onboarding_followups(company_id):
            await self.finalize_onboarding(company_id)
            return
        survey_status = survey_service.get_initial_survey_status(company_id)
        answers = [
            SurveyAnswerCreate(
                question_id=a.question_id,
                question_text=a.question_text,
                answer_type=a.answer_type,
                respondent_role=a.respondent_role,
                raw_answer=a.raw_answer,
                numeric_value=a.numeric_value,
                answer_json=a.answer_json,
                response_id=a.response_id,
            )
            for a in survey_status.answers
        ]
        await self.run_agent_onboarding(company_id, answers)


onboarding_service = OnboardingService()
