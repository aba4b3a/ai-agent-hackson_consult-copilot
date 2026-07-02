from pydantic import BaseModel, Field


class WorkspaceContext(BaseModel):
    """Company-specific context used to interpret a source document."""

    workspace_name: str = ""
    business_description: str = ""
    products: list[str] = Field(default_factory=list)
    customer_segments: list[str] = Field(default_factory=list)
    competitors: list[str] = Field(default_factory=list)
    known_issues: list[str] = Field(default_factory=list)
    kpis: list[str] = Field(default_factory=list)
    observation_topics: list[str] = Field(default_factory=list)


class ExtractionRequest(BaseModel):
    source_type: str
    body: str
    workspace: WorkspaceContext = Field(default_factory=WorkspaceContext)


class ExtractedObservation(BaseModel):
    summary: str
    quote: str
    confidence: float = Field(ge=0.0, le=1.0)
    related_entities: list[str] = Field(default_factory=list)
    # Observations are observed facts. Hypotheses live in a separate list so
    # facts and inferences are never mixed (Requirement 6).
    fact_or_hypothesis: str = "fact"


class ExtractedHypothesis(BaseModel):
    statement: str
    confidence: float = Field(ge=0.0, le=1.0)
    recommended_observations: list[str] = Field(default_factory=list)


# Controlled vocabulary for the knowledge graph (Requirement 9).
ENTITY_TYPES = (
    "CustomerSegment",
    "Product",
    "Issue",
    "Competitor",
    "CompetitiveEvent",
    "KPI",
)
RELATIONSHIP_TYPES = (
    "MENTIONS",
    "HAS_ISSUE",
    "RELATES_TO",
    "COMPETES_WITH",
    "MAY_CAUSE",
    "IMPACTS",
    "SUPPORTS",
    "CONTRADICTS",
)


class ExtractedEntity(BaseModel):
    # entity_id and workspace_id are assigned by back/ on persistence; the
    # agent only extracts type, name, and aliases (Requirement 5, 7.4).
    name: str
    entity_type: str
    aliases: list[str] = Field(default_factory=list)


class ExtractedRelationship(BaseModel):
    # Endpoints reference entities by name; back/ resolves them to entity_ids
    # during normalization (7.5).
    from_entity: str
    to_entity: str
    relationship_type: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class ExtractionPayload(BaseModel):
    """The portion of the result the model is asked to produce."""

    observations: list[ExtractedObservation] = Field(default_factory=list)
    hypotheses: list[ExtractedHypothesis] = Field(default_factory=list)
    entities: list[ExtractedEntity] = Field(default_factory=list)
    relationships: list[ExtractedRelationship] = Field(default_factory=list)


class ExtractionResult(ExtractionPayload):
    # "gemini" when produced by a live model call, "mock" for the deterministic
    # keyword fallback.
    extraction_method: str = "mock"


class FollowupRequest(BaseModel):
    """Context for generating conversational follow-up questions (R12.4)."""

    workspace: WorkspaceContext = Field(default_factory=WorkspaceContext)
    # Answers collected so far in the conversation (most recent last).
    answers: list[str] = Field(default_factory=list)


class FollowupPayload(BaseModel):
    """The portion of the follow-up result the model is asked to produce."""

    questions: list[str] = Field(default_factory=list)


class FollowupResponse(FollowupPayload):
    # "gemini" when produced by a live model call, "mock" for the fallback.
    generation_method: str = "mock"


class CopilotContext(BaseModel):
    """Retrieved knowledge passed to the Copilot for grounding (R16)."""

    facts: list[str] = Field(default_factory=list)
    hypotheses: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    workspace: WorkspaceContext = Field(default_factory=WorkspaceContext)


class CopilotAnswerRequest(BaseModel):
    question: str
    context: CopilotContext = Field(default_factory=CopilotContext)


class CopilotAnswerPayload(BaseModel):
    """The portion of the Copilot answer the model is asked to produce.

    Observed facts and hypotheses are kept separate (R16); evidence references
    are attached by back/ from what it retrieved, not fabricated by the model.
    """

    answer: str = ""
    observed_facts: list[str] = Field(default_factory=list)
    hypotheses: list[str] = Field(default_factory=list)
    recommended_observations: list[str] = Field(default_factory=list)


class CopilotAnswerResult(CopilotAnswerPayload):
    # "gemini" when produced by a live model call, "mock" for the fallback.
    answer_method: str = "mock"
