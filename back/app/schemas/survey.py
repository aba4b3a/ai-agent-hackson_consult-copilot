from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Frequency = Literal['daily', 'weekly', 'monthly', 'quarterly', 'event_based', 'ad_hoc']
AnswerType = Literal[
    'single_choice',
    'multiple_choice',
    'numeric',
    'text',
    'long_text',
    'rating',
    'date',
    'json',
]


class SurveyChoice(BaseModel):
    value: str
    label: str
    description: str | None = None


class SurveyValidation(BaseModel):
    required: bool = True
    min_value: float | None = None
    max_value: float | None = None
    min_length: int | None = None
    max_length: int | None = None
    unit: str | None = None
    step: float | None = None


class SurveyQuestion(BaseModel):
    question_id: str
    company_id: str
    version: str = 'v1'
    question_order: int
    question_text: str
    short_label: str
    help_text: str | None = None
    target_role: str
    answer_type: AnswerType
    frequency: Frequency
    question_category: str
    purpose: str
    placeholder: str | None = None
    choices: list[SurveyChoice] = Field(default_factory=list)
    validation: SurveyValidation = Field(default_factory=SurveyValidation)
    related_kpi_domains: list[str] = Field(default_factory=list)
    related_focus_metric_categories: list[str] = Field(default_factory=list)
    qualitative_intent: str | None = None
    quantitative_intent: str | None = None
    related_node_types: list[str] = Field(default_factory=list)
    related_edge_types: list[str] = Field(default_factory=list)
    options: list[str] = Field(default_factory=list)


class SurveyTemplate(BaseModel):
    template_id: str
    company_id: str
    survey_type: str
    version: str
    title: str
    description: str
    storage_path: str
    questions: list[SurveyQuestion]


class SurveyAnswerCreate(BaseModel):
    question_id: str
    question_text: str
    answer_type: AnswerType
    respondent_role: str
    raw_answer: str
    numeric_value: float | None = None
    answer_json: dict[str, Any] = Field(default_factory=dict)


class SurveySubmissionCreate(BaseModel):
    respondent_role: str = 'owner'
    answers: list[SurveyAnswerCreate]
    chat_transcript: list[dict[str, str]] = Field(default_factory=list)


class SurveySubmissionResult(BaseModel):
    company_id: str
    answer_count: int
    raw_storage: dict
    response_results: list[dict]


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


class SurveyAnswerRead(BaseModel):
    question_id: str
    question_text: str
    answer_type: AnswerType
    respondent_role: str
    raw_answer: str
    numeric_value: float | None = None
    answer_json: dict[str, Any] = Field(default_factory=dict)
    collected_at: str


class InitialSurveyStatus(BaseModel):
    company_id: str
    answered: bool
    answered_count: int
    total_count: int
    answers: list[SurveyAnswerRead] = Field(default_factory=list)
    onboarding_status: str | None = None
    onboarding_error: str | None = None
