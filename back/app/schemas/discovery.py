from pydantic import BaseModel, Field


class WorkspaceCreate(BaseModel):
    workspace_name: str
    business_description: str = ""
    products: list[str] = Field(default_factory=list)
    customer_segments: list[str] = Field(default_factory=list)
    competitors: list[str] = Field(default_factory=list)
    known_issues: list[str] = Field(default_factory=list)
    kpis: list[str] = Field(default_factory=list)
    observation_topics: list[str] = Field(default_factory=list)


class Workspace(WorkspaceCreate):
    workspace_id: str
    status: str = "active"


class ReportFormCreate(BaseModel):
    workspace_id: str
    target_role: str = "field_staff"
    focus_topics: list[str] = Field(default_factory=list)
    due_date: str | None = None


class ReportForm(BaseModel):
    form_id: str
    workspace_id: str
    url: str
    target_role: str
    focus_topics: list[str]
    due_date: str | None = None
    questions: list[str]


class ReportSubmissionCreate(BaseModel):
    form_id: str
    submitted_by_role: str = "field_staff"
    free_text: str
    customer_type: str = "unknown"
    product: str = "unknown"
    issue_category: str = "unknown"
    competitor: str | None = None
    kpi_note: str | None = None


class VoiceIntakeCreate(BaseModel):
    workspace_id: str
    submitted_by_role: str = "field_staff"
    transcript: str


class Source(BaseModel):
    source_id: str
    workspace_id: str
    source_type: str
    title: str
    body: str
    processing_status: str
    source_uri: str


class Observation(BaseModel):
    observation_id: str
    workspace_id: str
    source_id: str
    source_type: str
    # ISO8601 timestamp used for weekly discovery aggregation (§11).
    observed_at: str = ""
    summary: str
    quote: str
    fact_or_hypothesis: str = "fact"
    confidence: float
    related_entities: list[str]
    evidence_uri: str


class Hypothesis(BaseModel):
    hypothesis_id: str
    workspace_id: str
    statement: str
    status: str
    confidence: float
    supporting_observation_ids: list[str]
    recommended_observations: list[str]


class DiscoverySignal(BaseModel):
    signal_id: str
    workspace_id: str
    signal_type: str
    metric_name: str
    current_value: float
    baseline_value: float
    change_rate: float
    related_entities: list[str]
    evidence_count: int
    severity: str


class DashboardMetrics(BaseModel):
    sources_ingested: int
    observations_extracted: int
    entities_formed: int
    relationships_created: int
    hypotheses_under_observation: int
    evidence_coverage: float


class Dashboard(BaseModel):
    workspace: Workspace
    metrics: DashboardMetrics
    signals: list[DiscoverySignal]
    observations: list[Observation]
    hypotheses: list[Hypothesis]


class EvidenceResult(BaseModel):
    source_id: str
    observation_id: str | None = None
    title: str
    source_type: str
    snippet: str
    tags: list[str]
    confidence: float
    evidence_uri: str


class GraphNode(BaseModel):
    id: str
    type: str
    label: str
    summary: str


class GraphEdge(BaseModel):
    source: str
    target: str
    type: str
    evidence_count: int
    fact_or_hypothesis: str


class GraphSlice(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    summary: str


class WeeklyReport(BaseModel):
    report_id: str
    workspace_id: str
    period: str
    summary: str
    observed_facts: list[str]
    hypotheses: list[str]
    evidence: list[EvidenceResult]
    recommended_observations: list[str]
    limitations: list[str]


class FollowupRequest(BaseModel):
    workspace_id: str
    answers: list[str] = Field(default_factory=list)


class FollowupResponse(BaseModel):
    questions: list[str] = Field(default_factory=list)


class WeeklyReportPayload(BaseModel):
    """Agent weekly-report response (evidence is attached by back, not the model)."""

    summary: str = ""
    observed_facts: list[str] = Field(default_factory=list)
    hypotheses: list[str] = Field(default_factory=list)
    recommended_observations: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class CopilotAnswerPayload(BaseModel):
    """Agent copilot response (evidence is attached by back, not the model)."""

    answer: str = ""
    observed_facts: list[str] = Field(default_factory=list)
    hypotheses: list[str] = Field(default_factory=list)
    recommended_observations: list[str] = Field(default_factory=list)


class CopilotAsk(BaseModel):
    workspace_id: str
    question: str


class CopilotAnswer(BaseModel):
    answer: str
    observed_facts: list[str]
    hypotheses: list[str]
    evidence: list[EvidenceResult]
    recommended_observations: list[str]
