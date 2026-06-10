from pydantic import BaseModel, Field


class QualityRun(BaseModel):
    quality_run_id: str
    quality_score: int = Field(ge=0, le=100)
    release_decision: str
    risk_level: str
