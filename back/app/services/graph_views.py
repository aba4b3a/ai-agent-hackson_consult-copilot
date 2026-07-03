"""View-specific knowledge graph slices over in-memory data (§12).

Builds bounded graph slices for the consultant graph viewer from accumulated
extraction entities/relationships plus co-occurrence within observations.
Fact edges and hypothesis edges are kept distinct so the UI can render
hypotheses dashed (R6). BigQuery Graph is the phase-2 backend; this module is
the in-memory equivalent of the graph slice API (design §10.4).
"""

from __future__ import annotations

from collections import defaultdict
from itertools import combinations

from app.schemas.discovery import (
    GraphEdge,
    GraphNode,
    GraphSlice,
    Hypothesis,
    Observation,
    Workspace,
)
from app.schemas.extraction import ExtractedEntity, ExtractedRelationship

VIEWS = ("customer-issue", "competitor-impact", "kpi-causal", "hypothesis")
DEFAULT_VIEW = VIEWS[0]

_MAX_NODES = 12
_MAX_EDGES = 20

# Entity types participating in each view.
_VIEW_TYPES: dict[str, set[str]] = {
    "customer-issue": {"CustomerSegment", "Issue"},
    "competitor-impact": {"Competitor", "Issue", "Product"},
    "kpi-causal": {"Issue", "KPI"},
}

# Relationship types treated as hypotheses (rendered dashed).
_HYPOTHESIS_EDGE_TYPES = {"MAY_CAUSE"}

_TYPE_LABELS = {
    "CustomerSegment": "顧客層",
    "Product": "商品・サービス",
    "Issue": "課題",
    "Competitor": "競合",
    "KPI": "KPI",
    "Hypothesis": "仮説",
}


def build_graph_slice(
    view: str,
    workspace: Workspace,
    entities: dict[str, ExtractedEntity],
    relationships: list[ExtractedRelationship],
    observations: list[Observation],
    hypotheses: list[Hypothesis],
) -> GraphSlice:
    if view not in VIEWS:
        view = DEFAULT_VIEW

    types = _entity_types(workspace, entities)

    if view == "hypothesis":
        nodes, edges = _hypothesis_view(types, observations, hypotheses)
    else:
        nodes, edges = _typed_view(_VIEW_TYPES[view], types, relationships, observations)

    nodes, edges = _bound(nodes, edges)
    return GraphSlice(nodes=nodes, edges=edges, summary=_summary(view, edges))


def _entity_types(
    workspace: Workspace, entities: dict[str, ExtractedEntity]
) -> dict[str, str]:
    """Resolve entity name -> type from extraction results and setup context."""
    types: dict[str, str] = {}
    for name in workspace.customer_segments:
        types[name] = "CustomerSegment"
    for name in workspace.products:
        types[name] = "Product"
    for name in workspace.competitors:
        types[name] = "Competitor"
    for name in workspace.kpis:
        types[name] = "KPI"
    for name in workspace.known_issues:
        types[name] = "Issue"
    for name, entity in entities.items():
        types.setdefault(name, entity.entity_type)
    return types


def _typed_view(
    target_types: set[str],
    types: dict[str, str],
    relationships: list[ExtractedRelationship],
    observations: list[Observation],
) -> tuple[list[GraphNode], list[GraphEdge]]:
    def type_of(name: str) -> str:
        return types.get(name, "Issue")

    def in_view(name: str) -> bool:
        return type_of(name) in target_types

    # Co-occurrence within one observation counts as factual evidence that two
    # entities relate (§11/§12); pair order is normalized.
    cooccurrence: dict[tuple[str, str], int] = defaultdict(int)
    for obs in observations:
        members = sorted({e for e in obs.related_entities if in_view(e)})
        for a, b in combinations(members, 2):
            if type_of(a) != type_of(b):  # cross-type pairs only
                cooccurrence[(a, b)] += 1

    # Typed relationships accumulated from extraction.
    edges: dict[tuple[str, str], GraphEdge] = {}
    for rel in relationships:
        if not (in_view(rel.from_entity) and in_view(rel.to_entity)):
            continue
        low, high = sorted((rel.from_entity, rel.to_entity))
        key = (low, high)
        is_hypothesis = rel.relationship_type in _HYPOTHESIS_EDGE_TYPES
        existing = edges.get(key)
        if existing is not None:
            existing.evidence_count += 1
            continue
        edges[key] = GraphEdge(
            source=rel.from_entity,
            target=rel.to_entity,
            type=rel.relationship_type,
            evidence_count=1,
            fact_or_hypothesis="hypothesis" if is_hypothesis else "fact",
        )

    for (a, b), count in cooccurrence.items():
        existing = edges.get((a, b))
        if existing is not None:
            existing.evidence_count += count
            continue
        edges[(a, b)] = GraphEdge(
            source=a,
            target=b,
            type="RELATES_TO",
            evidence_count=count,
            fact_or_hypothesis="fact",
        )

    node_names = {name for edge in edges.values() for name in (edge.source, edge.target)}
    # Show isolated in-view entities too, so a sparse view is not empty.
    node_names.update(name for name in types if type_of(name) in target_types)
    nodes = [_node(name, type_of(name)) for name in sorted(node_names)]
    return nodes, list(edges.values())


def _hypothesis_view(
    types: dict[str, str],
    observations: list[Observation],
    hypotheses: list[Hypothesis],
) -> tuple[list[GraphNode], list[GraphEdge]]:
    obs_by_id = {obs.observation_id: obs for obs in observations}
    nodes: dict[str, GraphNode] = {}
    edges: list[GraphEdge] = []

    for hypothesis in hypotheses:
        nodes[hypothesis.hypothesis_id] = GraphNode(
            id=hypothesis.hypothesis_id,
            type="Hypothesis",
            label=hypothesis.statement,
            summary="観察中の仮説",
        )
        related: dict[str, int] = defaultdict(int)
        for obs_id in hypothesis.supporting_observation_ids:
            obs = obs_by_id.get(obs_id)
            if obs is None:
                continue
            for entity in obs.related_entities:
                related[entity] += 1
        for entity, count in related.items():
            entity_type = types.get(entity, "Issue")
            nodes.setdefault(entity, _node(entity, entity_type))
            edges.append(
                GraphEdge(
                    source=entity,
                    target=hypothesis.hypothesis_id,
                    type="SUPPORTS",
                    evidence_count=count,
                    fact_or_hypothesis="hypothesis",
                )
            )
    return list(nodes.values()), edges


def _node(name: str, entity_type: str) -> GraphNode:
    return GraphNode(
        id=name,
        type=entity_type,
        label=name,
        summary=_TYPE_LABELS.get(entity_type, entity_type),
    )


def _bound(
    nodes: list[GraphNode], edges: list[GraphEdge]
) -> tuple[list[GraphNode], list[GraphEdge]]:
    edges = sorted(edges, key=lambda e: e.evidence_count, reverse=True)[:_MAX_EDGES]
    connected = {name for edge in edges for name in (edge.source, edge.target)}
    # Prefer connected nodes, then isolated ones, up to the cap.
    ordered = sorted(nodes, key=lambda n: (n.id not in connected, n.id))
    kept = ordered[:_MAX_NODES]
    kept_ids = {n.id for n in kept}
    edges = [e for e in edges if e.source in kept_ids and e.target in kept_ids]
    return kept, edges


def _summary(view: str, edges: list[GraphEdge]) -> str:
    facts = [e for e in edges if e.fact_or_hypothesis == "fact"]
    hypos = [e for e in edges if e.fact_or_hypothesis == "hypothesis"]
    parts = [f"事実の関係 {len(facts)} 件、仮説の関係 {len(hypos)} 件を表示しています。"]
    if facts:
        top = max(facts, key=lambda e: e.evidence_count)
        parts.append(
            f"最も証拠が多い関連は「{top.source}」と「{top.target}」（{top.evidence_count} 件）です。"
        )
    if view == "kpi-causal":
        parts.append("表示は共起・言及に基づく関連であり、因果を確定するものではありません。")
    return "".join(parts)
