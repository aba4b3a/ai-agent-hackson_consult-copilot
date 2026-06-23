from typing import Any, Literal
from pydantic import BaseModel, Field

Frequency = Literal['daily', 'weekly', 'monthly', 'quarterly', 'event_based', 'ad_hoc']
AnswerType = Literal['single_choice', 'multiple_choice', 'numeric', 'text', 'rating', 'date', 'json']


class SurveyQuestion(BaseModel):
    question_id: str
    company_id: str
    question_text: str
    target_role: str
    answer_type: AnswerType
    frequency: Frequency
    qualitative_intent: str | None = None
    quantitative_intent: str | None = None
    related_node_types: list[str] = Field(default_factory=list)
    related_edge_types: list[str] = Field(default_factory=list)
    options: list[str] = Field(default_factory=list)


class SurveyResponseCreate(BaseModel):
    question_id: str
    respondent_role: str
    question_text: str
    answer_type: AnswerType
    raw_answer: str
    survey_frequency: Frequency = 'ad_hoc'
    numeric_value: float | None = None
    answer_json: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class SurveyResponseRecord(SurveyResponseCreate):
    response_id: str
    company_id: str
    collected_at: str
    qualitative_summary: str | None = None
    quantitative_summary: str | None = None
    related_node_ids: list[str] = Field(default_factory=list)
    related_edge_ids: list[str] = Field(default_factory=list)


class SurveyResponseCreateResult(BaseModel):
    response: SurveyResponseRecord
    extracted_nodes: list[dict]
    extracted_edges: list[dict]
    persistence: dict
