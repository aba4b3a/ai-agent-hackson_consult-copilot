"""Follow-Up Agent: generate conversational follow-up questions (R12.4).

Uses Gemini structured output when configured, and falls back to a
deterministic set of policy-aligned questions otherwise so local development
and tests run without a live model call.
"""

from __future__ import annotations

import logging
from pathlib import Path

from agents.gemini import build_client
from app.config import settings
from app.schemas import FollowupPayload, FollowupRequest, FollowupResponse, WorkspaceContext

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "followup_questions.md"

_MAX_QUESTIONS = 3

# Deterministic fallback questions, aligned with the §5.4 topics.
_FALLBACK_QUESTIONS = [
    "それは普段と比べてどう違いましたか。原因に心当たりはありますか。",
    "どの顧客層・商品・競合名と関係していましたか。",
    "売上や再来店などの業務への影響につながりそうですか。",
]

_logger = logging.getLogger(__name__)


def generate_followups(request: FollowupRequest) -> FollowupResponse:
    if settings.use_gemini:
        return _gemini_followups(request)
    return _mock_followups(request)


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _build_prompt(request: FollowupRequest) -> str:
    ws = request.workspace
    context = [
        f"会社名: {ws.workspace_name or '不明'}",
        f"事業内容: {ws.business_description or '不明'}",
        f"顧客層: {'、'.join(ws.customer_segments) or '不明'}",
        f"商品・サービス: {'、'.join(ws.products) or '不明'}",
        f"競合: {'、'.join(ws.competitors) or '不明'}",
        f"重点観測項目: {'、'.join(ws.observation_topics) or '不明'}",
    ]
    answers = "\n".join(f"- {a}" for a in request.answers) or "（まだ回答なし）"
    return "\n".join(
        [
            _load_prompt(),
            "",
            "## 企業コンテキスト",
            *context,
            "",
            "## これまでの回答",
            answers,
        ]
    )


def _gemini_followups(request: FollowupRequest) -> FollowupResponse:
    from google.genai import types

    try:
        client = build_client()
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=_build_prompt(request),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=FollowupPayload,
            ),
        )
        payload = response.parsed
    except Exception:  # noqa: BLE001 - any SDK/API error degrades to mock
        _logger.warning("Follow-up generation failed; falling back to mock", exc_info=True)
        return _mock_followups(request)

    if not isinstance(payload, FollowupPayload):
        return _mock_followups(request)
    return FollowupResponse(
        questions=payload.questions[:_MAX_QUESTIONS],
        generation_method="gemini",
    )


def _mock_followups(request: FollowupRequest) -> FollowupResponse:
    questions = list(_FALLBACK_QUESTIONS)
    # Prefer a workspace observation topic if one is defined and not obviously
    # already covered, keeping the set concise.
    topic = _first_uncovered_topic(request.workspace, request.answers)
    if topic:
        questions.insert(0, f"「{topic}」に関係する具体的な発言や変化はありましたか。")
    return FollowupResponse(
        questions=questions[:_MAX_QUESTIONS],
        generation_method="mock",
    )


def _first_uncovered_topic(workspace: WorkspaceContext, answers: list[str]) -> str | None:
    joined = " ".join(answers)
    for topic in workspace.observation_topics:
        if topic and topic not in joined:
            return topic
    return None
