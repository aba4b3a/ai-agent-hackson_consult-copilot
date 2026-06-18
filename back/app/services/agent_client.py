"""Client for the agent knowledge-extraction service.

In mock mode, or when the agent service is unreachable, extraction falls back
to a local keyword-based implementation so seeding, tests, and startup never
depend on the agent being up.
"""

from __future__ import annotations

import httpx

from app.core.config import settings
from app.schemas.discovery import Workspace
from app.schemas.extraction import (
    ExtractedEntity,
    ExtractedHypothesis,
    ExtractedObservation,
    ExtractedRelationship,
    ExtractionResult,
)

_EXTRACT_PATH = "/v1/knowledge/extract"
_TIMEOUT = httpx.Timeout(10.0, connect=2.0)

# Generic fallback vocabulary used by the local extractor when the workspace
# context does not provide entity hints. Mirrors agent/agents/knowledge_agent.py.
_FALLBACK_VOCAB = ["価格", "待ち時間", "在庫", "オンライン", "競合", "クレーム"]


def get_agent_base_url() -> str:
    return settings.agent_base_url


def extract_knowledge(source_type: str, body: str, workspace: Workspace) -> ExtractionResult:
    if settings.mock_mode:
        return _local_extract(source_type, body, workspace)
    try:
        response = httpx.post(
            f"{settings.agent_base_url}{_EXTRACT_PATH}",
            json={
                "source_type": source_type,
                "body": body,
                "workspace": _workspace_payload(workspace),
            },
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        return ExtractionResult.model_validate(response.json())
    except (httpx.HTTPError, ValueError):
        # Resilient fallback: the agent may be down or returned bad data.
        return _local_extract(source_type, body, workspace)


def _workspace_payload(workspace: Workspace) -> dict[str, object]:
    return {
        "workspace_name": workspace.workspace_name,
        "business_description": workspace.business_description,
        "products": workspace.products,
        "customer_segments": workspace.customer_segments,
        "competitors": workspace.competitors,
        "known_issues": workspace.known_issues,
        "kpis": workspace.kpis,
        "observation_topics": workspace.observation_topics,
    }


def _local_extract(source_type: str, body: str, workspace: Workspace) -> ExtractionResult:
    vocab = _local_vocab(workspace)
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
    relationships = _local_relationships(entities)

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


def _local_vocab(workspace: Workspace) -> list[str]:
    terms: list[str] = []
    terms.extend(workspace.customer_segments)
    terms.extend(workspace.competitors)
    terms.extend(workspace.products)
    terms.extend(workspace.kpis)
    terms.extend(workspace.known_issues)
    terms.extend(workspace.observation_topics)
    terms.extend(_FALLBACK_VOCAB)
    return list(dict.fromkeys(terms))


def _entity_type_for(term: str, workspace: Workspace) -> str:
    if term in workspace.competitors:
        return "Competitor"
    if term in workspace.customer_segments:
        return "CustomerSegment"
    if term in workspace.products:
        return "Product"
    if term in workspace.kpis:
        return "KPI"
    return "Issue"


def _local_relationships(entities: list[ExtractedEntity]) -> list[ExtractedRelationship]:
    by_type: dict[str, list[str]] = {}
    for entity in entities:
        by_type.setdefault(entity.entity_type, []).append(entity.name)

    relationships: list[ExtractedRelationship] = []
    for segment in by_type.get("CustomerSegment", []):
        for issue in by_type.get("Issue", []):
            relationships.append(
                ExtractedRelationship(
                    from_entity=segment, to_entity=issue, relationship_type="MENTIONS"
                )
            )
    for issue in by_type.get("Issue", []):
        for competitor in by_type.get("Competitor", []):
            relationships.append(
                ExtractedRelationship(
                    from_entity=issue, to_entity=competitor, relationship_type="RELATES_TO"
                )
            )
    return relationships
