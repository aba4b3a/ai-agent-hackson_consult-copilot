"""Research service: distribute Research Agent follow-up questions in-app.

In-app distribution only:
  - Cloud Scheduler -> Pub/Sub -> back tick() materializes assignments.
  - Front polls ``GET /companies/{id}/research/assignments`` per role.
  - Everything (questions, assignments, submitted answers) lives in the
    company's own BigQuery tenant dataset — no Firestore involved.

Email/Slack channels are out of scope and tracked separately.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from google.api_core.exceptions import NotFound

from app.core.config import settings
from app.crud.bigquery_crud import bigquery_crud
from app.crud.storage_crud import storage_crud
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

_ensured_companies: set[str] = set()

# Knowledge-formation tables that Research iteratively fills in: any
# `approval_status = 'proposed'` row missing one of its detail fields, or
# still below the confidence threshold, becomes a follow-up question. This is
# the primary loop the Research screen exists to drive — the ad-hoc
# agent-authored follow-ups are a secondary source of questions.
_GAP_TARGETS: list[dict[str, Any]] = [
    {
        "table": "kpi_candidates",
        "id_field": "kpi_candidate_id",
        "name_field": "kpi_name",
        "category": "KPI確認",
        "checked_fields": [
            ("calculation_hint", "算出方法"),
            ("data_source_hint", "データの取得元"),
            ("measurement_frequency", "計測頻度"),
        ],
    },
    {
        "table": "focus_metric_candidates",
        "id_field": "focus_metric_candidate_id",
        "name_field": "metric_name",
        "category": "注目指標確認",
        "checked_fields": [
            ("calculation_hint", "算出方法"),
            ("data_source_hint", "データの取得元"),
            ("trigger_condition", "着目すべき変化の条件"),
        ],
    },
    {
        "table": "observation_signals",
        "id_field": "observation_signal_id",
        "name_field": "signal_name",
        "category": "シグナル確認",
        "checked_fields": [
            ("detection_rule", "検知条件"),
            ("expected_source", "情報の入手元"),
            ("expected_frequency", "確認頻度"),
        ],
    },
]

_LOW_CONFIDENCE_THRESHOLD = 0.7
_GAP_QUESTION_COOLDOWN_DAYS = 14
_CONFIDENCE_BUMP = 0.15


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _schedule_path(company_id: str) -> str:
    # Same GCS layout the agent writes to (tenants/{company_id}/...) — see
    # agent/tools/storage_tools.py's register_research_schedule_item.
    return f"tenants/{company_id}/research/schedule.json"


def _period_bucket(frequency: str, at: datetime) -> str:
    if frequency == "daily":
        return at.strftime("%Y-%m-%d")
    if frequency == "monthly":
        return at.strftime("%Y-%m")
    # weekly (and unrecognized values) bucket by ISO year-week.
    return at.strftime("%G-W%V")


def _table(company_id: str, table: str) -> str:
    return settings.qualified_table(company_id, table)


def _ensure_tables(company_id: str) -> None:
    if company_id in _ensured_companies or settings.dry_run:
        _ensured_companies.add(company_id)
        return
    dataset = settings.dataset_id()
    questions_table = settings.company_table(company_id, QUESTIONS_TABLE)
    assignments_table = settings.company_table(company_id, ASSIGNMENTS_TABLE)
    answer_events_table = settings.company_table(company_id, "followup_answer_events")
    ddl = f"""
CREATE SCHEMA IF NOT EXISTS `{settings.project_id}.{dataset}`;

CREATE TABLE IF NOT EXISTS `{settings.project_id}.{dataset}.{questions_table}` (
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
  target_candidate_table STRING,
  target_candidate_id STRING,
  target_candidate_name STRING,
  created_at TIMESTAMP NOT NULL
);

ALTER TABLE `{settings.project_id}.{dataset}.{questions_table}`
  ADD COLUMN IF NOT EXISTS target_candidate_table STRING,
  ADD COLUMN IF NOT EXISTS target_candidate_id STRING,
  ADD COLUMN IF NOT EXISTS target_candidate_name STRING;

CREATE TABLE IF NOT EXISTS `{settings.project_id}.{dataset}.{assignments_table}` (
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

CREATE TABLE IF NOT EXISTS `{settings.project_id}.{dataset}.{answer_events_table}` (
  followup_answer_event_id STRING NOT NULL,
  company_id STRING NOT NULL,
  followup_question_id STRING NOT NULL,
  question_text STRING,
  respondent_role STRING,
  answered_at TIMESTAMP NOT NULL,
  answer_text STRING,
  answer_payload JSON,
  extracted_summary STRING,
  extracted_entities JSON,
  extracted_signals JSON,
  source_gcs_uri STRING,
  source_file_generation STRING,
  created_at TIMESTAMP NOT NULL
);
""".strip()
    bigquery_crud.execute_sql(ddl)
    _ensured_companies.add(company_id)


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
            "target_candidate_table": data.target_candidate_table,
            "target_candidate_id": data.target_candidate_id,
            "target_candidate_name": data.target_candidate_name,
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
        # Only the real research_assignments columns — Assignment also carries
        # question_text/target_candidate_* fields that are joined in for
        # display and don't exist on this table.
        row = {
            "assignment_id": assignment.assignment_id,
            "company_id": assignment.company_id,
            "followup_question_id": assignment.followup_question_id,
            "target_role": assignment.target_role,
            "target_user_id": assignment.target_user_id,
            "status": assignment.status,
            "created_at": assignment.created_at,
            "expected_response_by": assignment.expected_response_by,
            "answered_at": assignment.answered_at,
            "followup_answer_event_id": assignment.followup_answer_event_id,
        }
        _insert_row(_table(data.company_id, ASSIGNMENTS_TABLE), row)
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
        if status in (None, "open"):
            items = items + self._resolve_scheduled_assignments(company_id, target_role)
        return AssignmentList(
            company_id=company_id, target_role=target_role, items=items, total=len(items)
        )

    def _read_schedule(self, company_id: str) -> list[dict[str, Any]]:
        """Read the Knowledge-Agent-authored collection schedule from GCS
        (tenants/{company_id}/research/schedule.json). Absent file just means
        no recurring collection has been set up yet for this company."""
        try:
            payload = storage_crud.read_json(_schedule_path(company_id))
        except (FileNotFoundError, NotFound):
            return []
        items = payload.get("items", [])
        return items if isinstance(items, list) else []

    def _already_collected(self, company_id: str, table_name: str, period: str) -> bool:
        sql = f"""
SELECT 1 FROM `{_table(company_id, table_name)}`
WHERE company_id = {sql_literal(company_id)} AND period = {sql_literal(period)}
LIMIT 1
""".strip()
        try:
            return bool(bigquery_crud.query_rows(sql))
        except NotFound:
            # The agent hasn't created this collection table yet.
            return False

    def _resolve_scheduled_assignments(
        self, company_id: str, target_role: str | None
    ) -> list[Assignment]:
        """Resolve the GCS-stored collection schedule into "due now" items,
        at Research-page display time — no cron pre-materialization needed
        for this path. An item is due when its current period (daily/weekly/
        monthly bucket) has no observation row yet in its collection table."""
        now = datetime.now(timezone.utc)
        resolved: list[Assignment] = []
        for item in self._read_schedule(company_id):
            if target_role is not None and item.get("target_role") != target_role:
                continue
            table_name = item.get("table_name")
            schedule_item_id = item.get("schedule_item_id")
            if not table_name or not schedule_item_id:
                continue
            period = _period_bucket(item.get("frequency", "weekly"), now)
            if self._already_collected(company_id, table_name, period):
                continue
            resolved.append(
                Assignment(
                    assignment_id=schedule_item_id,
                    company_id=company_id,
                    followup_question_id=schedule_item_id,
                    target_role=item.get("target_role", "owner"),
                    status="open",
                    created_at=item.get("updated_at", utc_now_iso()),
                    question_text=item.get("question_text"),
                    question_category="定期収集",
                    reason=item.get("purpose"),
                    expected_answer_format=item.get("value_type"),
                    target_candidate_table=item.get("target_candidate_table"),
                    target_candidate_id=item.get("target_candidate_id"),
                    target_candidate_name=item.get("target_candidate_name"),
                )
            )
        return resolved

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
        if data.assignment_id.startswith("sched_"):
            return self._submit_scheduled_answer(company_id, data)
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
            "answer_payload": json.dumps(data.answer_payload, ensure_ascii=False),
            "extracted_summary": None,
            "extracted_entities": json.dumps({}, ensure_ascii=False),
            "extracted_signals": json.dumps({}, ensure_ascii=False),
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

        question = self.get_question(company_id, assignment["followup_question_id"])
        if question and question.get("target_candidate_table") and question.get("target_candidate_id"):
            self._bump_candidate_confidence(
                company_id, question["target_candidate_table"], question["target_candidate_id"]
            )

        return FollowupAnswerResult(
            assignment_id=data.assignment_id,
            followup_answer_event_id=followup_answer_event_id,
            bigquery_write_result=bq_result,
            assignment_status="answered",
        )

    def _submit_scheduled_answer(
        self, company_id: str, data: FollowupAnswerSubmit
    ) -> FollowupAnswerResult:
        """Answer for a GCS-schedule-driven item: write straight into the
        collection table the Knowledge Agent created for it (there's no
        research_assignments row to update — the schedule resolves live)."""
        item = next(
            (i for i in self._read_schedule(company_id) if i.get("schedule_item_id") == data.assignment_id),
            None,
        )
        if item is None:
            raise KeyError(data.assignment_id)
        table_name = item["table_name"]
        answered_at = data.answered_at or utc_now_iso()
        period = _period_bucket(item.get("frequency", "weekly"), datetime.now(timezone.utc))
        observation_id = _new_id("obs")
        value: float | None = None
        if item.get("value_type") == "number":
            try:
                value = float(data.answer_text.strip())
            except ValueError:
                value = None
        row = {
            "observation_id": observation_id,
            "company_id": company_id,
            "period": period,
            "observed_at": answered_at,
            "respondent_role": data.respondent_role,
            "raw_answer": data.answer_text,
            "value": value,
            "properties": json.dumps(data.answer_payload, ensure_ascii=False),
            "created_at": answered_at,
        }
        try:
            bq_result = bigquery_crud.insert_json_rows(_table(company_id, table_name), [row])
        except NotFound as exc:
            raise KeyError(f"collection table {table_name} not found for {company_id}") from exc
        return FollowupAnswerResult(
            assignment_id=data.assignment_id,
            followup_answer_event_id=observation_id,
            bigquery_write_result=bq_result,
            assignment_status="answered",
        )

    def _bump_candidate_confidence(self, company_id: str, table: str, candidate_id: str) -> None:
        """A submitted answer is evidence the row is better-supported now, so
        nudge its confidence up. Actual field extraction (calculation_hint,
        data_source_hint, ...) still requires Knowledge Agent review before
        promotion — this only closes the confidence half of the gap."""
        id_field = next((t["id_field"] for t in _GAP_TARGETS if t["table"] == table), None)
        if id_field is None:
            return
        sql = f"""
UPDATE `{_table(company_id, table)}`
SET confidence = LEAST(1.0, IFNULL(confidence, 0.0) + {_CONFIDENCE_BUMP}),
    updated_at = CURRENT_TIMESTAMP()
WHERE company_id = {sql_literal(company_id)} AND {id_field} = {sql_literal(candidate_id)}
""".strip()
        bigquery_crud.execute_sql(sql)

    def _has_recent_gap_question(self, company_id: str, candidate_id: str) -> bool:
        sql = f"""
SELECT 1 FROM `{_table(company_id, QUESTIONS_TABLE)}`
WHERE target_candidate_id = {sql_literal(candidate_id)}
  AND generated_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {_GAP_QUESTION_COOLDOWN_DAYS} DAY)
LIMIT 1
""".strip()
        return bool(bigquery_crud.query_rows(sql))

    def _create_gap_question(
        self,
        company_id: str,
        target: dict[str, Any],
        candidate_id: str,
        candidate_name: str,
        confidence: float | None,
        missing_labels: list[str],
    ) -> dict[str, Any]:
        if missing_labels:
            question_text = f"「{candidate_name}」の{'・'.join(missing_labels)}を教えてください。"
        else:
            question_text = f"「{candidate_name}」は現在の実態と合っていますか？裏付けとなる情報があれば教えてください。"
        reason = (
            f"{target['table']}の「{candidate_name}」がまだ確定していません"
            f"(confidence={confidence if confidence is not None else '未設定'})。"
        )
        data = FollowupQuestionCreate(
            company_id=company_id,
            followup_question_id=_new_id("fq"),
            question_text=question_text,
            question_category=target["category"],
            target_role="owner",
            reason=reason,
            priority_score=round(1.0 - (confidence or 0.0), 2),
            expected_answer_format="自由記述",
            target_candidate_table=target["table"],
            target_candidate_id=candidate_id,
            target_candidate_name=candidate_name,
        )
        return self.register_followup_question(data)

    def generate_gap_questions(self, company_id: str) -> dict[str, Any]:
        """Scan the knowledge-formation candidate tables for still-`proposed`
        rows that are missing detail fields or below the confidence
        threshold, and register a follow-up question for each gap that
        hasn't already been asked recently."""
        _ensure_tables(company_id)
        created: list[dict[str, Any]] = []
        for target in _GAP_TARGETS:
            columns = [target["id_field"], target["name_field"], "confidence"] + [
                field for field, _ in target["checked_fields"]
            ]
            sql = f"""
SELECT {", ".join(columns)}
FROM `{_table(company_id, target["table"])}`
WHERE company_id = {sql_literal(company_id)} AND approval_status = 'proposed'
""".strip()
            try:
                rows = bigquery_crud.query_rows(sql)
            except NotFound:
                # This candidate table hasn't been created for the company
                # yet (e.g. observation_signals predates onboarding) — skip
                # it rather than failing the whole gap-detection pass.
                continue
            for row in rows:
                candidate_id = row[target["id_field"]]
                candidate_name = row[target["name_field"]]
                confidence = row.get("confidence")
                missing_labels = [
                    label for field, label in target["checked_fields"] if not row.get(field)
                ]
                is_low_confidence = confidence is None or confidence < _LOW_CONFIDENCE_THRESHOLD
                if not missing_labels and not is_low_confidence:
                    continue
                if self._has_recent_gap_question(company_id, candidate_id):
                    continue
                created.append(
                    self._create_gap_question(
                        company_id, target, candidate_id, candidate_name, confidence, missing_labels
                    )
                )
        return {"created_count": len(created), "items": created}

    def tick(self, company_id: str, cohort: str = "all") -> dict[str, Any]:
        """Materialize assignments for every proposed follow-up question that
        doesn't already have an open assignment, scoped to one company.

        Runs gap-detection first so newly-registered questions (from
        knowledge-table rows still missing data) are picked up in the same
        tick, then expands each proposed question to a single assignment for
        its target_role. A future iteration could pull role->user mapping
        from a directory table.
        """
        _ensure_tables(company_id)
        gap_result = self.generate_gap_questions(company_id)
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
        return {
            "cohort": cohort,
            "created_count": len(created),
            "items": created,
            "gap_questions_created": gap_result["created_count"],
        }


research_service = ResearchService()
