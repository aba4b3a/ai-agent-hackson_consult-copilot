"""Back-side mirror of the agent's knowledge extraction contract.

The agent service is the source of truth for the extraction logic; this module
defines how back/ parses its HTTP response. Keep these models in sync with
`agent/app/schemas.py`.
"""

from pydantic import BaseModel, Field


class ExtractedObservation(BaseModel):
    summary: str
    quote: str = ""
    confidence: float = 0.5
    related_entities: list[str] = Field(default_factory=list)
    fact_or_hypothesis: str = "fact"


class ExtractedHypothesis(BaseModel):
    statement: str
    confidence: float = 0.5
    recommended_observations: list[str] = Field(default_factory=list)


class ExtractedEntity(BaseModel):
    name: str
    entity_type: str
    aliases: list[str] = Field(default_factory=list)


class ExtractedRelationship(BaseModel):
    from_entity: str
    to_entity: str
    relationship_type: str
    confidence: float = 0.5


class ExtractionResult(BaseModel):
    observations: list[ExtractedObservation] = Field(default_factory=list)
    hypotheses: list[ExtractedHypothesis] = Field(default_factory=list)
    entities: list[ExtractedEntity] = Field(default_factory=list)
    relationships: list[ExtractedRelationship] = Field(default_factory=list)
    extraction_method: str = "mock"
