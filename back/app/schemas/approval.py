from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


ApprovalStatus = Literal["pending", "approved", "rejected", "applied", "cancelled"]
ApprovalTargetType = Literal[
    "kpi_candidate",
    "focus_metric_candidate",
    "custom_table",
    "wiki_update",
    "schema_migration",
    "observation_signal",
    "other",
]


class ApprovalCreate(BaseModel):
    company_id: str
    target_type: ApprovalTargetType
    target_id: str
    title: str
    summary: str = ""
    proposed_payload: dict[str, Any] = Field(default_factory=dict)
    diff_payload: dict[str, Any] | None = None
    confidence: float | None = None
    reason: str | None = None
    created_by: str = "agent:knowledge_agent"


class ApprovalDecision(BaseModel):
    decided_by: str = Field(..., description="User id or email that approved/rejected")
    decision_note: str | None = None


class ApprovalRecord(BaseModel):
    approval_id: str
    company_id: str
    target_type: ApprovalTargetType
    target_id: str
    title: str
    summary: str
    proposed_payload: dict[str, Any]
    diff_payload: dict[str, Any] | None = None
    confidence: float | None = None
    reason: str | None = None
    status: ApprovalStatus
    created_by: str
    created_at: str
    decided_by: str | None = None
    decided_at: str | None = None
    decision_note: str | None = None
    applied_at: str | None = None
    applied_result: dict[str, Any] | None = None


class ApprovalList(BaseModel):
    company_id: str
    items: list[ApprovalRecord]
    total: int
    status_filter: ApprovalStatus | None = None


class ApprovalApplyResult(BaseModel):
    approval_id: str
    status: ApprovalStatus
    applied_result: dict[str, Any]
