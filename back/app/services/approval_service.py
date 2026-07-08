"""Approval service: human-in-the-loop review of KPI/focus metric proposals.

All approval records live in the company's own BigQuery tenant dataset
(``approvals`` table) — no Firestore involved.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

from app.core.config import settings
from app.crud.bigquery_crud import bigquery_crud
from app.schemas.approval import (
    ApprovalApplyResult,
    ApprovalCreate,
    ApprovalDecision,
    ApprovalRecord,
    ApprovalStatus,
)
from app.utils.bigquery_sql import sql_literal
from app.utils.time import utc_now_iso

TABLE = "approvals"

_TIMESTAMP_FIELDS = ("created_at", "decided_at", "applied_at")
_JSON_FIELDS = ("proposed_payload", "diff_payload", "applied_result")

_ensured_companies: set[str] = set()


def _new_id(target_type: str) -> str:
    return f"appr_{target_type}_{uuid.uuid4().hex[:12]}"


def _table(company_id: str) -> str:
    return settings.qualified_table(company_id, TABLE)


def _ensure_table(company_id: str) -> None:
    if company_id in _ensured_companies or settings.dry_run:
        _ensured_companies.add(company_id)
        return
    dataset = settings.dataset_id()
    approvals_table = settings.company_table(company_id, TABLE)
    ddl = f"""
CREATE SCHEMA IF NOT EXISTS `{settings.project_id}.{dataset}`;

CREATE TABLE IF NOT EXISTS `{settings.project_id}.{dataset}.{approvals_table}` (
  approval_id STRING NOT NULL,
  company_id STRING NOT NULL,
  target_type STRING NOT NULL,
  target_id STRING NOT NULL,
  title STRING NOT NULL,
  summary STRING,
  proposed_payload JSON,
  diff_payload JSON,
  confidence FLOAT64,
  reason STRING,
  status STRING NOT NULL,
  created_by STRING NOT NULL,
  created_at TIMESTAMP NOT NULL,
  decided_by STRING,
  decided_at TIMESTAMP,
  decision_note STRING,
  applied_at TIMESTAMP,
  applied_result JSON
);
""".strip()
    bigquery_crud.execute_sql(ddl)
    _ensured_companies.add(company_id)


def _insert_row(table: str, row: dict) -> None:
    if settings.dry_run:
        return
    columns = list(row.keys())
    values_sql = ", ".join(sql_literal(row[column]) for column in columns)
    sql = f"INSERT INTO `{table}` ({', '.join(columns)}) VALUES ({values_sql})"
    bigquery_crud.execute_sql(sql)


def _row_to_record(row: dict) -> ApprovalRecord:
    normalized = dict(row)
    for field in _TIMESTAMP_FIELDS:
        value = normalized.get(field)
        if isinstance(value, datetime):
            normalized[field] = value.isoformat()
    for field in _JSON_FIELDS:
        value = normalized.get(field)
        if isinstance(value, str):
            normalized[field] = json.loads(value) if value else None
    return ApprovalRecord(**normalized)


class ApprovalService:
    def create(self, data: ApprovalCreate) -> ApprovalRecord:
        _ensure_table(data.company_id)
        record = ApprovalRecord(
            approval_id=_new_id(data.target_type),
            company_id=data.company_id,
            target_type=data.target_type,
            target_id=data.target_id,
            title=data.title,
            summary=data.summary,
            proposed_payload=data.proposed_payload,
            diff_payload=data.diff_payload,
            confidence=data.confidence,
            reason=data.reason,
            status="pending",
            created_by=data.created_by,
            created_at=utc_now_iso(),
        )
        _insert_row(_table(data.company_id), record.model_dump())
        return record

    def list(
        self,
        company_id: str,
        status: ApprovalStatus | None = None,
        limit: int | None = 100,
    ) -> list[ApprovalRecord]:
        _ensure_table(company_id)
        clauses = [f"company_id = {sql_literal(company_id)}"]
        if status is not None:
            clauses.append(f"status = {sql_literal(status)}")
        sql = (
            f"SELECT * FROM `{_table(company_id)}` WHERE {' AND '.join(clauses)} "
            f"ORDER BY created_at DESC LIMIT {int(limit) if limit else 1000}"
        )
        rows = bigquery_crud.query_rows(sql)
        return [_row_to_record(row) for row in rows]

    def get(self, company_id: str, approval_id: str) -> ApprovalRecord | None:
        _ensure_table(company_id)
        sql = (
            f"SELECT * FROM `{_table(company_id)}` "
            f"WHERE approval_id = {sql_literal(approval_id)} LIMIT 1"
        )
        rows = bigquery_crud.query_rows(sql)
        return _row_to_record(rows[0]) if rows else None

    def _transition(
        self,
        company_id: str,
        approval_id: str,
        next_status: ApprovalStatus,
        decision: ApprovalDecision,
    ) -> ApprovalRecord:
        existing = self.get(company_id, approval_id)
        if existing is None:
            raise KeyError(approval_id)
        if existing.status != "pending":
            raise ValueError(
                f"approval {approval_id} is not pending (current status={existing.status})"
            )
        decided_at = utc_now_iso()
        sql = f"""
UPDATE `{_table(company_id)}`
SET status = {sql_literal(next_status)},
    decided_by = {sql_literal(decision.decided_by)},
    decided_at = {sql_literal(decided_at)},
    decision_note = {sql_literal(decision.decision_note)}
WHERE approval_id = {sql_literal(approval_id)}
""".strip()
        bigquery_crud.execute_sql(sql)
        updated = self.get(company_id, approval_id)
        assert updated is not None
        return updated

    def approve(
        self, company_id: str, approval_id: str, decision: ApprovalDecision
    ) -> ApprovalRecord:
        return self._transition(company_id, approval_id, "approved", decision)

    def reject(
        self, company_id: str, approval_id: str, decision: ApprovalDecision
    ) -> ApprovalRecord:
        return self._transition(company_id, approval_id, "rejected", decision)

    def mark_applied(
        self, company_id: str, approval_id: str, applied_result: dict[str, Any]
    ) -> ApprovalApplyResult:
        existing = self.get(company_id, approval_id)
        if existing is None:
            raise KeyError(approval_id)
        if existing.status != "approved":
            raise ValueError(
                f"approval {approval_id} must be approved before apply "
                f"(current status={existing.status})"
            )
        applied_at = utc_now_iso()
        sql = f"""
UPDATE `{_table(company_id)}`
SET status = 'applied',
    applied_at = {sql_literal(applied_at)},
    applied_result = {sql_literal(applied_result)}
WHERE approval_id = {sql_literal(approval_id)}
""".strip()
        bigquery_crud.execute_sql(sql)
        return ApprovalApplyResult(
            approval_id=approval_id, status="applied", applied_result=applied_result
        )


approval_service = ApprovalService()
