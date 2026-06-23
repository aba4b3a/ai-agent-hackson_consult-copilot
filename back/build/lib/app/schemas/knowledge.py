from typing import Any
from pydantic import BaseModel, Field


class KnowledgeNode(BaseModel):
    node_id: str
    company_id: str
    node_type: str
    label: str
    description: str = ''
    source_response_id: str | None = None
    confidence: float = 0.5
    properties: dict[str, Any] = Field(default_factory=dict)


class KnowledgeEdge(BaseModel):
    edge_id: str
    company_id: str
    source_node_id: str
    target_node_id: str
    edge_type: str
    description: str = ''
    source_response_id: str | None = None
    confidence: float = 0.5
    strength: float | None = None
    observed_count: int = 1
    properties: dict[str, Any] = Field(default_factory=dict)


class CustomTableRequest(BaseModel):
    table_id: str
    purpose: str
    columns: list[dict]


class CustomTableProposal(BaseModel):
    company_id: str
    table_id: str
    purpose: str
    ddl: str
    wiki_update_markdown: str
    recommended_questions: list[dict]
    human_review_required: bool = True
