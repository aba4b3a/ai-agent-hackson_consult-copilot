from typing import Any, Literal
from pydantic import BaseModel, Field

Frequency = Literal["daily", "weekly", "monthly", "quarterly", "event_based", "ad_hoc"]
AnswerType = Literal["single_choice", "multiple_choice", "numeric", "text", "rating", "date", "json"]


class SurveyQuestion(BaseModel):
    question_id: str
    company_id: str
    question_text: str
    target_role: str = Field(description="owner, manager, staff, sales, consultant, etc.")
    answer_type: AnswerType
    frequency: Frequency
    qualitative_intent: str | None = None
    quantitative_intent: str | None = None
    related_node_types: list[str] = []
    related_edge_types: list[str] = []
    options: list[str] = []


class SurveyResponse(BaseModel):
    response_id: str
    company_id: str
    question_id: str
    respondent_role: str
    collected_at: str
    raw_answer: str
    numeric_value: float | None = None
    answer_json: dict[str, Any] = {}
    qualitative_summary: str | None = None
    quantitative_summary: str | None = None


class KnowledgeNode(BaseModel):
    node_id: str
    company_id: str
    node_type: str = Field(description="Person, Process, Product, CustomerSegment, TacitKnowledge, KPI, Signal, Risk, Skill, Question")
    label: str
    description: str = ""
    source_response_id: str | None = None
    confidence: float = 0.5
    properties: dict[str, Any] = {}


class KnowledgeEdge(BaseModel):
    edge_id: str
    company_id: str
    source_node_id: str
    target_node_id: str
    edge_type: str = Field(description="KNOWS, PERFORMS, IMPACTS, INDICATES, MEASURES, RELATED_TO, DEPENDS_ON, TRANSFERS_TO")
    description: str = ""
    source_response_id: str | None = None
    confidence: float = 0.5
    properties: dict[str, Any] = {}


class KnowledgeExtractionResult(BaseModel):
    company_id: str
    nodes: list[KnowledgeNode]
    edges: list[KnowledgeEdge]
    recommended_questions: list[SurveyQuestion]
    wiki_markdown: str
    wiki_json: dict[str, Any]
