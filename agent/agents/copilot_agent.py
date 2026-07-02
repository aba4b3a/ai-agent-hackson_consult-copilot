"""Report Copilot: answer consultant questions grounded in stored knowledge.

Uses Gemini structured output when configured, and falls back to a
deterministic answer built from the provided context otherwise so local
development and tests run without a live model call. Observed facts and
hypotheses are kept separate (R16); the model never fabricates evidence —
back/ attaches evidence references from what it retrieved.
"""

from __future__ import annotations

import logging
from pathlib import Path

from agents.gemini import build_client
from app.config import settings
from app.schemas import (
    CopilotAnswerPayload,
    CopilotAnswerRequest,
    CopilotAnswerResult,
)

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "copilot_answer.md"

_logger = logging.getLogger(__name__)


def answer_question(request: CopilotAnswerRequest) -> CopilotAnswerResult:
    if settings.use_gemini:
        return _gemini_answer(request)
    return _mock_answer(request)


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _build_prompt(request: CopilotAnswerRequest) -> str:
    ctx = request.context
    ws = ctx.workspace
    facts = [f"- {f}" for f in ctx.facts] or ["（なし）"]
    hypotheses = [f"- {h}" for h in ctx.hypotheses] or ["（なし）"]
    evidence = [f"- {e}" for e in ctx.evidence] or ["（なし）"]
    return "\n".join(
        [
            _load_prompt(),
            "",
            "## 企業コンテキスト",
            f"会社名: {ws.workspace_name or '不明'}",
            f"事業内容: {ws.business_description or '不明'}",
            f"顧客層: {'、'.join(ws.customer_segments) or '不明'}",
            f"競合: {'、'.join(ws.competitors) or '不明'}",
            f"重点観測項目: {'、'.join(ws.observation_topics) or '不明'}",
            "",
            "## 観察事実（facts）",
            *facts,
            "",
            "## 仮説（hypotheses）",
            *hypotheses,
            "",
            "## 証拠（evidence）",
            *evidence,
            "",
            "## 質問",
            request.question,
        ]
    )


def _gemini_answer(request: CopilotAnswerRequest) -> CopilotAnswerResult:
    from google.genai import types

    try:
        client = build_client()
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=_build_prompt(request),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CopilotAnswerPayload,
            ),
        )
        payload = response.parsed
    except Exception:  # noqa: BLE001 - any SDK/API error degrades to mock
        _logger.warning("Copilot answer failed; falling back to mock", exc_info=True)
        return _mock_answer(request)

    if not isinstance(payload, CopilotAnswerPayload):
        return _mock_answer(request)
    return CopilotAnswerResult(
        answer=payload.answer,
        observed_facts=payload.observed_facts,
        hypotheses=payload.hypotheses,
        recommended_observations=payload.recommended_observations,
        answer_method="gemini",
    )


def _mock_answer(request: CopilotAnswerRequest) -> CopilotAnswerResult:
    ctx = request.context
    fact_line = ctx.facts[0] if ctx.facts else "現時点で十分な観察事実は蓄積されていません。"
    answer = (
        f"ご質問「{request.question}」について、現在の観察事実からは次が確認できます: {fact_line} "
        "原因は未確定のため、以下の仮説として扱い、追加観測で検証してください。"
    )
    return CopilotAnswerResult(
        answer=answer,
        observed_facts=ctx.facts[:5],
        hypotheses=ctx.hypotheses[:5],
        recommended_observations=[
            "競合名が出た発話で、価格・待ち時間・在庫のどれが理由か確認する",
            "変化が大きい顧客セグメントを特定する",
        ],
        answer_method="mock",
    )
