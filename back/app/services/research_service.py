"""Research service: distribute Research Agent follow-up questions in-app.

In-app distribution only:
  - Cloud Scheduler -> Pub/Sub -> back tick() materializes assignments.
  - Front polls ``GET /companies/{id}/research/assignments`` per role.
  - Submissions land in Firestore (assignment state) and BigQuery
    (``followup_answer_events`` event log).

Email/Slack channels are out of scope and tracked separately.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.crud.bigquery_crud import bigquery_crud
from app.db.firestore import firestore_repo
from app.schemas.research import (
    Assignment,
    AssignmentCreate,
    AssignmentList,
    AssignmentStatus,
    FollowupAnswerResult,
    FollowupAnswerSubmit,
    FollowupQuestionCreate,
)

ASSIGNMENT_COLLECTION = "research_assignments"
FOLLOWUP_QUESTION_COLLECTION = "research_followup_questions"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _tenant_dataset(company_id: str) -> str:
    safe = company_id.replace("-", "_").replace(".", "_")
    return f"cd_tenant_{safe}"


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ResearchService:
    def register_followup_question(self, data: FollowupQuestionCreate) -> dict[str, Any]:
        payload = data.model_dump()
        payload.update({"created_at": _now_iso(), "status": "proposed"})
        firestore_repo.set(FOLLOWUP_QUESTION_COLLECTION, data.followup_question_id, payload)
        bq_table = (
            f"{settings.project_id}.{_tenant_dataset(data.company_id)}.research_followup_question_events"
        )
        bq_row = {
            "followup_question_id": data.followup_question_id,
            "company_id": data.company_id,
            "generated_at": payload["created_at"],
            "question_text": data.question_text,
            "question_category": data.question_category,
            "target_role": data.target_role,
            "reason": data.reason,
            "related_kpi_candidates": data.related_kpi_candidates,
            "related_focus_metric_candidates": data.related_focus_metric_candidates,
            "expected_answer_format": data.expected_answer_format,
            "priority_score": data.priority_score,
            "status": "proposed",
            "source_answer_event_ids": data.source_answer_event_ids,
            "source_gcs_uri": None,
            "created_at": payload["created_at"],
        }
        bq_result = bigquery_crud.insert_json_rows(bq_table, [bq_row])
        return {"firestore": payload, "bigquery": bq_result}

    def assign(self, data: AssignmentCreate) -> Assignment:
        assignment = Assignment(
            assignment_id=_new_id("assign"),
            company_id=data.company_id,
            followup_question_id=data.followup_question_id,
            target_role=data.target_role,
            target_user_id=data.target_user_id,
            status="open",
            created_at=_now_iso(),
            expected_response_by=data.expected_response_by,
        )
        firestore_repo.set(
            ASSIGNMENT_COLLECTION, assignment.assignment_id, assignment.model_dump()
        )
        return assignment

    def list_assignments(
        self,
        company_id: str,
        target_role: str | None = None,
        status: AssignmentStatus | None = "open",
        limit: int = 200,
    ) -> AssignmentList:
        filters: dict[str, Any] = {"company_id": company_id}
        if target_role is not None:
            filters["target_role"] = target_role
        if status is not None:
            filters["status"] = status
        rows = firestore_repo.query(
            ASSIGNMENT_COLLECTION,
            filters=filters,
            order_by="created_at",
            descending=True,
            limit=limit,
        )
        items = [Assignment(**row) for row in rows]
        # Enrich items by joining the question text from FOLLOWUP_QUESTION_COLLECTION
        # — handled by the endpoint to keep this service single-purpose.
        return AssignmentList(
            company_id=company_id, target_role=target_role, items=items, total=len(items)
        )

    def get_question(self, followup_question_id: str) -> dict[str, Any] | None:
        return firestore_repo.get(FOLLOWUP_QUESTION_COLLECTION, followup_question_id)

    def submit_answer(self, company_id: str, data: FollowupAnswerSubmit) -> FollowupAnswerResult:
        assignment_dict = firestore_repo.get(ASSIGNMENT_COLLECTION, data.assignment_id)
        if assignment_dict is None:
            raise KeyError(data.assignment_id)
        assignment = Assignment(**assignment_dict)
        if assignment.company_id != company_id:
            raise PermissionError("Assignment does not belong to the requested company.")
        if assignment.status != "open":
            raise ValueError(
                f"assignment {data.assignment_id} is not open (status={assignment.status})"
            )

        followup_answer_event_id = _new_id("fans")
        answered_at = data.answered_at or _now_iso()

        bq_table = f"{settings.project_id}.{_tenant_dataset(company_id)}.followup_answer_events"
        bq_row = {
            "followup_answer_event_id": followup_answer_event_id,
            "company_id": company_id,
            "followup_question_id": assignment.followup_question_id,
            "question_text": None,
            "respondent_role": data.respondent_role,
            "answered_at": answered_at,
            "answer_text": data.answer_text,
            "answer_payload": data.answer_payload,
            "extracted_summary": None,
            "extracted_entities": {},
            "extracted_signals": {},
            "source_gcs_uri": None,
            "source_file_generation": None,
            "created_at": answered_at,
        }
        bq_result = bigquery_crud.insert_json_rows(bq_table, [bq_row])

        updated = firestore_repo.update(
            ASSIGNMENT_COLLECTION,
            data.assignment_id,
            {
                "status": "answered",
                "answered_at": answered_at,
                "followup_answer_event_id": followup_answer_event_id,
            },
        )
        return FollowupAnswerResult(
            assignment_id=data.assignment_id,
            followup_answer_event_id=followup_answer_event_id,
            bigquery_write_result=bq_result,
            assignment_status=updated["status"],
        )

    def tick(self, cohort: str = "all") -> dict[str, Any]:
        """Materialize assignments for every proposed follow-up question.

        For now we expand each proposed question to a single assignment for
        its target_role. A future iteration could pull role->user mapping
        from a directory table.
        """
        questions = firestore_repo.query(
            FOLLOWUP_QUESTION_COLLECTION,
            filters={"status": "proposed"},
            order_by="created_at",
            descending=False,
            limit=500,
        )
        created = []
        for question in questions:
            existing = firestore_repo.query(
                ASSIGNMENT_COLLECTION,
                filters={
                    "followup_question_id": question["followup_question_id"],
                    "status": "open",
                },
                limit=1,
            )
            if existing:
                continue
            assignment = self.assign(
                AssignmentCreate(
                    company_id=question["company_id"],
                    followup_question_id=question["followup_question_id"],
                    target_role=question["target_role"],
                    target_user_id=None,
                    expected_response_by=None,
                )
            )
            created.append(assignment.model_dump())
        return {"cohort": cohort, "created_count": len(created), "items": created}


research_service = ResearchService()
