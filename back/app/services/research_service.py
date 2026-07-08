"""Research service: distribute Research Agent follow-up questions in-app.

In-app distribution only:
  - Cloud Scheduler -> Pub/Sub -> back tick() materializes assignments.
  - Front polls ``GET /companies/{id}/research/assignments`` per role.
  - Everything (questions, assignments, submitted answers) lives in the
    company's own BigQuery tenant dataset — no Firestore involved.

Email/Slack channels are out of scope and tracked separately.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from app.core.config import settings
from app.crud.bigquery_crud import bigquery_crud
from app.schemas.research import (
    Assignment,
    AssignmentCreate,
    AssignmentList,
    AssignmentStatus,
    FollowupAnswerResult,
    FollowupAnswerSubmit,
    FollowupQuestionCreate,
)
from app.utils.bigquery_sql import sql_literal
from app.utils.time import utc_now_iso

QUESTIONS_TABLE = "research_followup_question_events"
ASSIGNMENTS_TABLE = "research_assignments"

_TIMESTAMP_FIELDS = ("created_at", "expected_response_by", "answered_at", "generated_at")

_ensured_datasets: set[str] = set()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _tenant_dataset(company_id: str) -> str:
    safe = company_id.replace("-", "_").replace(".", "_")
    return f"cd_tenant_{safe}"


def _table(company_id: str, table: str) -> str:
    return f"{settings.project_id}.{_tenant_dataset(company_id)}.{table}"


def _ensure_tables(company_id: str) -> None:
    dataset = _tenant_dataset(company_id)
    if dataset in _ensured_datasets or settings.dry_run:
        _ensured_datasets.add(dataset)
        return
    ddl = f"""
CREATE SCHEMA IF NOT EXISTS `{settings.project_id}.{dataset}`;

CREATE TABLE IF NOT EXISTS `{settings.project_id}.{dataset}.{QUESTIONS_TABLE}` (
  followup_question_id STRING NOT NULL,
  company_id STRING NOT NULL,
  generated_at TIMESTAMP NOT NULL,
  question_text STRING NOT NULL,
  question_category STRING,
  target_role STRING,
  reason STRING,
  related_kpi_candidates ARRAY<STRING>,
  related_focus_metric_candidates ARRAY<STRING>,
  expected_answer_format STRING,
  priority_score FLOAT64,
  status STRING,
  source_answer_event_ids ARRAY<STRING>,
  source_gcs_uri STRING,
  created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS `{settings.project_id}.{dataset}.{ASSIGNMENTS_TABLE}` (
  assignment_id STRING NOT NULL,
  company_id STRING NOT NULL,
  followup_question_id STRING NOT NULL,
  target_role STRING NOT NULL,
  target_user_id STRING,
  status STRING NOT NULL,
  created_at TIMESTAMP NOT NULL,
  expected_response_by TIMESTAMP,
  answered_at TIMESTAMP,
  followup_answer_event_id STRING
);
""".strip()
    bigquery_crud.execute_sql(ddl)
    _ensured_datasets.add(dataset)


def _insert_row(table: str, row: dict) -> dict:
    if settings.dry_run:
        return {"dry_run": True, "table": table, "row": row}
    columns = list(row.keys())
    values_sql = ", ".join(sql_literal(row[column]) for column in columns)
    sql = f"INSERT INTO `{table}` ({', '.join(columns)}) VALUES ({values_sql})"
    return bigquery_crud.execute_sql(sql)


def _stringify_timestamps(row: dict) -> dict:
    normalized = dict(row)
    for field in _TIMESTAMP_FIELDS:
        value = normalized.get(field)
        if isinstance(value, datetime):
            normalized[field] = value.isoformat()
    return normalized


class ResearchService:
    def register_followup_question(self, data: FollowupQuestionCreate) -> dict[str, Any]:
        _ensure_tables(data.company_id)
        now = utc_now_iso()
        row = {
            "followup_question_id": data.followup_question_id,
            "company_id": data.company_id,
            "generated_at": now,
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
            "created_at": now,
        }
        result = _insert_row(_table(data.company_id, QUESTIONS_TABLE), row)
        return {"bigquery": result, "row": row}

    def assign(self, data: AssignmentCreate) -> Assignment:
        _ensure_tables(data.company_id)
        assignment = Assignment(
            assignment_id=_new_id("assign"),
            company_id=data.company_id,
            followup_question_id=data.followup_question_id,
            target_role=data.target_role,
            target_user_id=data.target_user_id,
            status="open",
            created_at=utc_now_iso(),
            expected_response_by=data.expected_response_by,
        )
        _insert_row(_table(data.company_id, ASSIGNMENTS_TABLE), assignment.model_dump())
        return assignment

    def list_assignments(
        self,
        company_id: str,
        target_role: str | None = None,
        status: AssignmentStatus | None = "open",
        limit: int = 200,
    ) -> AssignmentList:
        _ensure_tables(company_id)
        clauses = [f"company_id = {sql_literal(company_id)}"]
        if target_role is not None:
            clauses.append(f"target_role = {sql_literal(target_role)}")
        if status is not None:
            clauses.append(f"status = {sql_literal(status)}")
        sql = (
            f"SELECT * FROM `{_table(company_id, ASSIGNMENTS_TABLE)}` "
            f"WHERE {' AND '.join(clauses)} ORDER BY created_at DESC LIMIT {int(limit)}"
        )
        rows = bigquery_crud.query_rows(sql)
        items = [Assignment(**_stringify_timestamps(row)) for row in rows]
        return AssignmentList(
            company_id=company_id, target_role=target_role, items=items, total=len(items)
        )

    def get_question(self, company_id: str, followup_question_id: str) -> dict[str, Any] | None:
        sql = (
            f"SELECT * FROM `{_table(company_id, QUESTIONS_TABLE)}` "
            f"WHERE followup_question_id = {sql_literal(followup_question_id)} LIMIT 1"
        )
        rows = bigquery_crud.query_rows(sql)
        return _stringify_timestamps(rows[0]) if rows else None

    def _get_assignment(self, company_id: str, assignment_id: str) -> dict[str, Any] | None:
        sql = (
            f"SELECT * FROM `{_table(company_id, ASSIGNMENTS_TABLE)}` "
            f"WHERE assignment_id = {sql_literal(assignment_id)} LIMIT 1"
        )
        rows = bigquery_crud.query_rows(sql)
        return _stringify_timestamps(rows[0]) if rows else None

    def submit_answer(self, company_id: str, data: FollowupAnswerSubmit) -> FollowupAnswerResult:
        _ensure_tables(company_id)
        assignment = self._get_assignment(company_id, data.assignment_id)
        if assignment is None:
            raise KeyError(data.assignment_id)
        if assignment["status"] != "open":
            raise ValueError(
                f"assignment {data.assignment_id} is not open (status={assignment['status']})"
            )

        followup_answer_event_id = _new_id("fans")
        answered_at = data.answered_at or utc_now_iso()

        bq_table = _table(company_id, "followup_answer_events")
        bq_row = {
            "followup_answer_event_id": followup_answer_event_id,
            "company_id": company_id,
            "followup_question_id": assignment["followup_question_id"],
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

        update_sql = f"""
UPDATE `{_table(company_id, ASSIGNMENTS_TABLE)}`
SET status = 'answered',
    answered_at = {sql_literal(answered_at)},
    followup_answer_event_id = {sql_literal(followup_answer_event_id)}
WHERE assignment_id = {sql_literal(data.assignment_id)}
""".strip()
        bigquery_crud.execute_sql(update_sql)

        return FollowupAnswerResult(
            assignment_id=data.assignment_id,
            followup_answer_event_id=followup_answer_event_id,
            bigquery_write_result=bq_result,
            assignment_status="answered",
        )

    def tick(self, company_id: str, cohort: str = "all") -> dict[str, Any]:
        """Materialize assignments for every proposed follow-up question that
        doesn't already have an open assignment, scoped to one company.

        For now we expand each proposed question to a single assignment for
        its target_role. A future iteration could pull role->user mapping
        from a directory table.
        """
        _ensure_tables(company_id)
        sql = f"""
SELECT q.followup_question_id, q.company_id, q.target_role
FROM `{_table(company_id, QUESTIONS_TABLE)}` q
WHERE q.status = 'proposed'
  AND NOT EXISTS (
    SELECT 1 FROM `{_table(company_id, ASSIGNMENTS_TABLE)}` a
    WHERE a.followup_question_id = q.followup_question_id AND a.status = 'open'
  )
""".strip()
        questions = bigquery_crud.query_rows(sql)
        created = []
        for question in questions:
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
