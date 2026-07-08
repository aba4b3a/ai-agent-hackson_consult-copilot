from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


AssignmentStatus = Literal["open", "answered", "skipped", "expired"]


class FollowupQuestionCreate(BaseModel):
    company_id: str
    followup_question_id: str
    question_text: str
    question_category: str | None = None
    target_role: str
    reason: str | None = None
    related_kpi_candidates: list[str] = Field(default_factory=list)
    related_focus_metric_candidates: list[str] = Field(default_factory=list)
    expected_answer_format: str | None = None
    priority_score: float = 0.0
    source_answer_event_ids: list[str] = Field(default_factory=list)


class AssignmentCreate(BaseModel):
    company_id: str
    followup_question_id: str
    target_role: str
    target_user_id: str | None = None
    expected_response_by: str | None = None


class Assignment(BaseModel):
    assignment_id: str
    company_id: str
    followup_question_id: str
    target_role: str
    target_user_id: str | None = None
    status: AssignmentStatus
    created_at: str
    expected_response_by: str | None = None
    answered_at: str | None = None
    followup_answer_event_id: str | None = None
    # Joined in from the question record by the list_assignments endpoint so
    # the UI can render the question without an extra round-trip.
    question_text: str | None = None
    question_category: str | None = None
    reason: str | None = None
    expected_answer_format: str | None = None


class AssignmentList(BaseModel):
    company_id: str
    target_role: str | None = None
    items: list[Assignment]
    total: int


class FollowupAnswerSubmit(BaseModel):
    assignment_id: str
    respondent_role: str
    answer_text: str
    answer_payload: dict[str, Any] = Field(default_factory=dict)
    answered_at: str | None = None


class FollowupAnswerResult(BaseModel):
    assignment_id: str
    followup_answer_event_id: str
    bigquery_write_result: dict[str, Any]
    assignment_status: AssignmentStatus
