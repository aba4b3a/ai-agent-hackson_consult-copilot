from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


SignalApproval = Literal["proposed", "approved", "rejected"]


class ObservationSignalCreate(BaseModel):
    observation_signal_id: str
    company_id: str
    signal_name: str
    signal_category: str | None = None
    description: str = ""
    related_focus_metric_candidate_ids: list[str] = Field(default_factory=list)
    related_kpi_candidate_ids: list[str] = Field(default_factory=list)
    detection_rule: str | None = None
    expected_source: str | None = None
    expected_frequency: str | None = None
    severity: str | None = None
    reason: str = ""
    source_answer_event_ids: list[str] = Field(default_factory=list)
    source_followup_answer_event_ids: list[str] = Field(default_factory=list)
    source_gcs_uris: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class ObservationSignalBatch(BaseModel):
    company_id: str
    items: list[ObservationSignalCreate]


class ObservationSignalWriteResult(BaseModel):
    company_id: str
    inserted_count: int
    bigquery_write_result: dict[str, Any]
