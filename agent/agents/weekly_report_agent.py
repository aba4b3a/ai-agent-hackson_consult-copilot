"""Weekly Discovery Report generator (§13).

Uses Gemini structured output when configured, and falls back to a
deterministic report assembled from the provided context otherwise. Facts and
hypotheses stay separate (R6/R13); evidence references are attached by back/,
not fabricated by the model. Distinct from the QualityOps report_agent.
"""

from __future__ import annotations

import logging
from pathlib import Path

from agents.gemini import build_client
from app.config import settings
from app.schemas import WeeklyReportPayload, WeeklyReportRequest, WeeklyReportResult

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "weekly_report.md"

_logger = logging.getLogger(__name__)


def generate_report(request: WeeklyReportRequest) -> WeeklyReportResult:
    if settings.use_gemini:
        return _gemini_report(request)
    return _mock_report(request)


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _build_prompt(request: WeeklyReportRequest) -> str:
    ctx = request.context
    ws = ctx.workspace
    signals = [f"- {s}" for s in ctx.signals] or ["（なし）"]
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
            f"重点観測項目: {'、'.join(ws.observation_topics) or '不明'}",
            "",
            f"## 対象期間: {request.period or '直近1週間'}",
            "",
            "## 発見シグナル",
            *signals,
            "",
            "## 観察事実（facts）",
            *facts,
            "",
            "## 仮説（hypotheses）",
            *hypotheses,
            "",
            "## 証拠（evidence）",
            *evidence,
        ]
    )


def _gemini_report(request: WeeklyReportRequest) -> WeeklyReportResult:
    from google.genai import types

    try:
        client = build_client()
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=_build_prompt(request),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=WeeklyReportPayload,
            ),
        )
        payload = response.parsed
    except Exception:  # noqa: BLE001 - any SDK/API error degrades to mock
        _logger.warning("Weekly report generation failed; falling back to mock", exc_info=True)
        return _mock_report(request)

    if not isinstance(payload, WeeklyReportPayload):
        return _mock_report(request)
    return WeeklyReportResult(
        summary=payload.summary,
        observed_facts=payload.observed_facts,
        hypotheses=payload.hypotheses,
        recommended_observations=payload.recommended_observations,
        limitations=payload.limitations,
        report_method="gemini",
    )


def _mock_report(request: WeeklyReportRequest) -> WeeklyReportResult:
    ctx = request.context
    signal_line = ctx.signals[0] if ctx.signals else "今週は顕著な変化シグナルは検出されていません。"
    summary = (
        f"今週の主な変化: {signal_line} "
        "因果は未確定のため、関連する仮説を観察中として扱い、次週の観測で検証します。"
    )
    return WeeklyReportResult(
        summary=summary,
        observed_facts=ctx.facts[:5],
        hypotheses=ctx.hypotheses[:5],
        recommended_observations=[
            "競合名が出た発話で、価格・待ち時間・在庫のどれが理由か確認する",
            "新しく言及されたサービス・競合の背景を確認する",
        ],
        limitations=[
            "ルールベース検出のため、閾値未満の変化は含まれていません。",
            "仮説は観察中であり、確定した事業原因として扱いません。",
        ],
        report_method="mock",
    )
