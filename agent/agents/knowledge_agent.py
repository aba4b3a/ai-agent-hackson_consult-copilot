"""Knowledge Agent: extract observations and hypotheses from source text.

Uses Gemini structured output when configured, and falls back to a
deterministic keyword-based mock otherwise so local development and tests run
without a live model call. Observed facts and hypotheses are kept in separate
lists (Requirement 6).
"""

from __future__ import annotations

from pathlib import Path

from app.config import settings
from app.schemas import (
    ExtractedEntity,
    ExtractedHypothesis,
    ExtractedObservation,
    ExtractedRelationship,
    ExtractionPayload,
    ExtractionRequest,
    ExtractionResult,
    WorkspaceContext,
)

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "knowledge_extraction.md"

# Generic fallback vocabulary used by the mock when the workspace context does
# not provide entity hints.
_FALLBACK_VOCAB = ["価格", "待ち時間", "在庫", "オンライン", "競合", "クレーム"]


def extract_knowledge(request: ExtractionRequest) -> ExtractionResult:
    result = _gemini_extract(request) if settings.use_gemini else _mock_extract(request)
    # Within-extraction entity normalization (7.4): dedupe by normalized name
    # and merge aliases. Cross-source matching against existing entities is
    # back/'s responsibility during persistence.
    result.entities = _normalize_entities(result.entities)
    return result


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _build_prompt(request: ExtractionRequest) -> str:
    ws = request.workspace
    context = [
        f"会社名: {ws.workspace_name or '不明'}",
        f"事業内容: {ws.business_description or '不明'}",
        f"商品・サービス: {'、'.join(ws.products) or '不明'}",
        f"顧客層: {'、'.join(ws.customer_segments) or '不明'}",
        f"競合: {'、'.join(ws.competitors) or '不明'}",
        f"既知の課題: {'、'.join(ws.known_issues) or '不明'}",
        f"KPI: {'、'.join(ws.kpis) or '不明'}",
        f"重点観測項目: {'、'.join(ws.observation_topics) or '不明'}",
    ]
    return "\n".join(
        [
            _load_prompt(),
            "",
            "## 企業コンテキスト",
            *context,
            "",
            "## ソース種別",
            request.source_type,
            "",
            "## ソース本文",
            request.body,
        ]
    )


def _gemini_extract(request: ExtractionRequest) -> ExtractionResult:
    # Imported lazily so mock mode and tests do not require the SDK installed.
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.gemini_api_key)
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=_build_prompt(request),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ExtractionPayload,
        ),
    )
    payload = response.parsed
    if not isinstance(payload, ExtractionPayload):
        # Model returned nothing parseable; degrade to mock rather than fail.
        return _mock_extract(request)
    return ExtractionResult(
        observations=payload.observations,
        hypotheses=payload.hypotheses,
        entities=payload.entities,
        relationships=payload.relationships,
        extraction_method="gemini",
    )


def _mock_extract(request: ExtractionRequest) -> ExtractionResult:
    workspace = request.workspace
    body = request.body
    vocab = _mock_vocab(workspace)
    tags = [term for term in vocab if term in body] or ["顧客変化"]
    lines = body.splitlines()
    quote = (lines[0] if lines else body)[:160]

    observation = ExtractedObservation(
        summary=f"{'、'.join(tags[:3])}に関する現場観察が追加された。",
        quote=quote,
        confidence=0.78,
        related_entities=tags,
        fact_or_hypothesis="fact",
    )

    entities = [
        ExtractedEntity(name=tag, entity_type=_entity_type_for(tag, workspace)) for tag in tags
    ]
    relationships = _mock_relationships(entities)

    hypotheses: list[ExtractedHypothesis] = []
    competitor_hit = any(term in body for term in ("競合", "オンライン")) or any(
        competitor in body for competitor in workspace.competitors
    )
    if competitor_hit:
        hypotheses.append(
            ExtractedHypothesis(
                statement="競合の利便性訴求が、顧客の不安や乗り換え意向を強めている可能性がある。",
                confidence=0.61,
                recommended_observations=[
                    "競合名が出た場面で比較理由を確認する",
                    "課題とKPIへの影響を同じ報告で記録する",
                ],
            )
        )

    return ExtractionResult(
        observations=[observation],
        hypotheses=hypotheses,
        entities=entities,
        relationships=relationships,
        extraction_method="mock",
    )


def _mock_vocab(workspace: WorkspaceContext) -> list[str]:
    terms: list[str] = []
    terms.extend(workspace.customer_segments)
    terms.extend(workspace.competitors)
    terms.extend(workspace.products)
    terms.extend(workspace.kpis)
    terms.extend(workspace.known_issues)
    terms.extend(workspace.observation_topics)
    terms.extend(_FALLBACK_VOCAB)
    # Preserve order while removing duplicates.
    return list(dict.fromkeys(terms))


def _entity_type_for(term: str, workspace: WorkspaceContext) -> str:
    if term in workspace.competitors:
        return "Competitor"
    if term in workspace.customer_segments:
        return "CustomerSegment"
    if term in workspace.products:
        return "Product"
    if term in workspace.kpis:
        return "KPI"
    # known_issues, observation_topics, and fallback terms default to Issue.
    return "Issue"


def _mock_relationships(entities: list[ExtractedEntity]) -> list[ExtractedRelationship]:
    by_type: dict[str, list[str]] = {}
    for entity in entities:
        by_type.setdefault(entity.entity_type, []).append(entity.name)

    relationships: list[ExtractedRelationship] = []
    # CustomerSegment MENTIONS Issue.
    for segment in by_type.get("CustomerSegment", []):
        for issue in by_type.get("Issue", []):
            relationships.append(
                ExtractedRelationship(
                    from_entity=segment, to_entity=issue, relationship_type="MENTIONS"
                )
            )
    # Issue RELATES_TO Competitor.
    for issue in by_type.get("Issue", []):
        for competitor in by_type.get("Competitor", []):
            relationships.append(
                ExtractedRelationship(
                    from_entity=issue, to_entity=competitor, relationship_type="RELATES_TO"
                )
            )
    return relationships


def _normalize_entities(entities: list[ExtractedEntity]) -> list[ExtractedEntity]:
    deduped: dict[str, ExtractedEntity] = {}
    for entity in entities:
        key = entity.name.strip().casefold()
        if not key:
            continue
        existing = deduped.get(key)
        if existing is None:
            deduped[key] = entity
            continue
        for alias in entity.aliases:
            if alias not in existing.aliases:
                existing.aliases.append(alias)
    return list(deduped.values())
