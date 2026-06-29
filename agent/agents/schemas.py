from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Frequency = Literal["daily", "weekly", "monthly", "quarterly", "event_based", "ad_hoc"]
AnswerType = Literal["single_choice", "multiple_choice", "numeric", "text", "rating", "date", "json"]
ApprovalStatus = Literal["proposed", "approved", "rejected", "deprecated"]
RiskLevel = Literal["low", "medium", "high"]


class SurveyQuestion(BaseModel):
    question_id: str
    company_id: str
    question_text: str
    target_role: str = Field(description="owner, manager, staff, sales, consultant, etc.")
    answer_type: AnswerType
    frequency: Frequency
    qualitative_intent: str | None = None
    quantitative_intent: str | None = None
    related_node_types: list[str] = Field(default_factory=list)
    related_edge_types: list[str] = Field(default_factory=list)
    options: list[str] = Field(default_factory=list)


class SurveyResponse(BaseModel):
    response_id: str
    company_id: str
    question_id: str
    respondent_role: str
    collected_at: str
    raw_answer: str
    numeric_value: float | None = None
    answer_json: dict[str, Any] = Field(default_factory=dict)
    qualitative_summary: str | None = None
    quantitative_summary: str | None = None


class CompanyProfile(BaseModel):
    company_id: str
    business_summary: str = "unknown"
    customer_summary: str = "unknown"
    product_service_summary: str = "unknown"
    competition_summary: str = "unknown"
    operation_summary: str = "unknown"
    current_issues: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    source_refs: list[str] = Field(default_factory=list)


class KpiCandidate(BaseModel):
    kpi_candidate_id: str
    company_id: str
    kpi_name: str
    kpi_domain: str | None = None
    kpi_type: str | None = None
    description: str = ""
    calculation_hint: str | None = None
    data_source_hint: str | None = None
    measurement_frequency: Frequency | None = None
    reason: str = ""
    source_answer_event_ids: list[str] = Field(default_factory=list)
    source_followup_answer_event_ids: list[str] = Field(default_factory=list)
    source_gcs_uris: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    importance_score: float = 0.0
    approval_status: ApprovalStatus = "proposed"
    requires_human_review: bool = True


class FocusMetricCandidate(BaseModel):
    focus_metric_candidate_id: str
    company_id: str
    metric_name: str
    metric_category: str | None = None
    description: str = ""
    related_kpi_candidate_ids: list[str] = Field(default_factory=list)
    related_common_kpi_ids: list[str] = Field(default_factory=list)
    observation_signal_types: list[str] = Field(default_factory=list)
    calculation_hint: str | None = None
    data_source_hint: str | None = None
    measurement_frequency: Frequency | None = None
    trigger_condition: str | None = None
    followup_policy: str | None = None
    reason: str = ""
    source_answer_event_ids: list[str] = Field(default_factory=list)
    source_followup_answer_event_ids: list[str] = Field(default_factory=list)
    source_gcs_uris: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    priority_score: float = 0.0
    approval_status: ApprovalStatus = "proposed"
    requires_human_review: bool = True


class ResearchPlanItem(BaseModel):
    research_task_id: str
    target_role: str
    frequency: Frequency
    question_intent: str
    base_questions: list[str] = Field(default_factory=list)
    followup_policy: str | None = None
    related_kpi_candidates: list[str] = Field(default_factory=list)
    related_focus_metric_candidates: list[str] = Field(default_factory=list)
    priority_score: float = 0.0


class HumanReviewItem(BaseModel):
    item_type: str
    summary: str
    reason: str
    risk_level: RiskLevel = "medium"


class WikiFile(BaseModel):
    path: str
    content: str
    content_type: str = "text/markdown; charset=utf-8"


class BigQueryWritePlan(BaseModel):
    operation: str
    target_table: str
    record_count: int = 0
    requires_human_review: bool = True
    reason: str | None = None


class KnowledgeAgentOutput(BaseModel):
    company_profile: CompanyProfile
    kpi_candidates: list[KpiCandidate] = Field(default_factory=list)
    focus_metric_candidates: list[FocusMetricCandidate] = Field(default_factory=list)
    observation_policy: dict[str, Any] = Field(default_factory=dict)
    research_plan: list[ResearchPlanItem] = Field(default_factory=list)
    wiki_files: list[WikiFile] = Field(default_factory=list)
    bigquery_write_plan: list[BigQueryWritePlan] = Field(default_factory=list)
    human_review_items: list[HumanReviewItem] = Field(default_factory=list)


class ResearchQuestion(BaseModel):
    question_id: str
    question_text: str
    question_category: str
    reason: str
    expected_answer_format: str
    related_kpis: list[str] = Field(default_factory=list)
    related_focus_metrics: list[str] = Field(default_factory=list)


class ResearchAnswerResult(BaseModel):
    answered: bool = False
    answer_text: str | None = None
    answer_summary: str | None = None
    extracted_signals: list[dict[str, Any]] = Field(default_factory=list)
    needs_followup: bool = False
    recommended_followup_question: str | None = None


class ResearchAgentOutput(BaseModel):
    research_task_id: str
    target_role: str
    questions_to_ask: list[ResearchQuestion] = Field(default_factory=list)
    answer_result: ResearchAnswerResult | None = None
    handoff_to_knowledge_agent: dict[str, Any] = Field(default_factory=dict)


class KnowledgeNode(BaseModel):
    node_id: str
    company_id: str
    node_type: str = Field(
        description="Person, Process, Product, CustomerSegment, TacitKnowledge, KPI, Signal, Risk, Skill, Question"
    )
    label: str
    description: str = ""
    source_response_id: str | None = None
    confidence: float = 0.5
    properties: dict[str, Any] = Field(default_factory=dict)


class KnowledgeEdge(BaseModel):
    edge_id: str
    company_id: str
    source_node_id: str
    target_node_id: str
    edge_type: str = Field(
        description="KNOWS, PERFORMS, IMPACTS, INDICATES, MEASURES, RELATED_TO, DEPENDS_ON, TRANSFERS_TO"
    )
    description: str = ""
    source_response_id: str | None = None
    confidence: float = 0.5
    properties: dict[str, Any] = Field(default_factory=dict)


class KnowledgeExtractionResult(BaseModel):
    company_id: str
    nodes: list[KnowledgeNode] = Field(default_factory=list)
    edges: list[KnowledgeEdge] = Field(default_factory=list)
    recommended_questions: list[SurveyQuestion] = Field(default_factory=list)
    wiki_markdown: str = ""
    wiki_json: dict[str, Any] = Field(default_factory=dict)
