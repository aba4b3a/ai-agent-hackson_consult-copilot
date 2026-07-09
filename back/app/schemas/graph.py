"""Graph API (design §10.4〜10.6) のレスポンスモデル。"""
from typing import Any

from pydantic import BaseModel


class SliceNode(BaseModel):
    node_id: str
    node_type: str
    label: str | None = None
    description: str | None = None
    confidence: float | None = None
    status: str | None = None


class SliceEdge(BaseModel):
    source_node_id: str
    target_node_id: str
    edge_type: str
    strength: float | None = None
    observed_count: int | None = None
    description: str | None = None


class SliceMeta(BaseModel):
    truncated: bool
    center_node_id: str | None = None
    period: str
    source: str  # 'bigquery' | 'sample'


class GraphSliceResponse(BaseModel):
    nodes: list[SliceNode]
    edges: list[SliceEdge]
    meta: SliceMeta


class GraphEntity(BaseModel):
    node_id: str
    node_type: str
    label: str | None = None
    confidence: float | None = None


class AdjacentEdge(BaseModel):
    edge_id: str | None = None
    direction: str  # 'outgoing' | 'incoming'
    edge_type: str
    description: str | None = None
    strength: float | None = None
    observed_count: int | None = None
    other_node_id: str
    other_node_label: str | None = None
    source_response_id: str | None = None


class EvidenceItem(BaseModel):
    response_id: str
    question_text: str | None = None
    raw_answer: str | None = None
    respondent_role: str | None = None
    collected_at: str | None = None


class NodeDetailResponse(BaseModel):
    node_id: str
    node_type: str
    label: str | None = None
    description: str | None = None
    confidence: float | None = None
    status: str | None = None
    source_response_id: str | None = None
    properties: dict[str, Any] | None = None
    created_at: str | None = None
    updated_at: str | None = None
    adjacent_edges: list[AdjacentEdge]
    evidence: list[EvidenceItem]
    source: str  # 'bigquery' | 'sample'
