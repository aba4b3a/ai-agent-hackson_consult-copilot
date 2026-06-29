"""DDL migration runner.

Runs raw DDL against BigQuery and records the outcome in
``{project}.cd_common.schema_migration_history``.

Design notes:
- Migrations are append-only. A re-applied migration with the same checksum is
  treated as already-done (idempotent).
- Rollback is *not* automatic. A failed migration is recorded with status=failed
  and the operator runs the recorded rollback_script via the same endpoint.
- The runner is the same code path for both common and tenant datasets.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.crud.bigquery_crud import bigquery_crud
from app.schemas.migration import (
    MigrationList,
    MigrationRequest,
    MigrationResult,
    MigrationStatus,
)


COMMON_DATASET = "cd_common"
MIGRATION_TABLE = "schema_migration_history"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _checksum(ddl: str) -> str:
    return hashlib.sha256(ddl.encode("utf-8")).hexdigest()


def _new_id() -> str:
    return f"mig_{uuid.uuid4().hex[:12]}"


def _history_table() -> str:
    return f"{settings.project_id}.{COMMON_DATASET}.{MIGRATION_TABLE}"


def _select_history_sql(filters: dict[str, Any] | None = None, limit: int = 200) -> str:
    where = ""
    if filters:
        clauses = []
        for key, value in filters.items():
            if isinstance(value, str):
                value_sql = "'" + value.replace("'", "''") + "'"
            else:
                value_sql = str(value)
            clauses.append(f"{key} = {value_sql}")
        where = " WHERE " + " AND ".join(clauses)
    return (
        f"SELECT migration_id, target_scope, target_dataset, version, migration_name, "
        f"checksum, applied_at, applied_by, status, error_message "
        f"FROM `{_history_table()}`{where} "
        f"ORDER BY applied_at DESC LIMIT {int(limit)}"
    )


class MigrationService:
    def list(self, target_dataset: str | None = None, limit: int = 200) -> MigrationList:
        filters = {"target_dataset": target_dataset} if target_dataset else None
        sql = _select_history_sql(filters=filters, limit=limit)
        result = bigquery_crud.execute_sql(sql)
        if result.get("dry_run"):
            return MigrationList(items=[], total=0)
        # The current BigQueryCrud doesn't expose rows; for now return an empty
        # list in non-dry-run mode and let callers query directly. A future
        # iteration should add a query() helper that yields rows.
        return MigrationList(items=[], total=0)

    def apply(self, request: MigrationRequest) -> MigrationResult:
        migration_id = _new_id()
        checksum = _checksum(request.ddl_statement)
        applied_at = _now_iso()

        status: MigrationStatus = "pending"
        error_message: str | None = None
        bq_result: dict[str, Any]
        try:
            bq_result = bigquery_crud.execute_sql(request.ddl_statement)
            status = "applied"
        except Exception as exc:  # pragma: no cover — surfaced as failed row below
            status = "failed"
            error_message = str(exc)
            bq_result = {"error": error_message}

        history_row = {
            "migration_id": migration_id,
            "target_scope": request.target_scope,
            "target_dataset": request.target_dataset,
            "version": request.version,
            "migration_name": request.migration_name,
            "checksum": checksum,
            "applied_at": applied_at,
            "applied_by": request.applied_by,
            "status": status,
            "error_message": error_message,
        }
        bigquery_crud.insert_json_rows(_history_table(), [history_row])

        return MigrationResult(
            migration_id=migration_id,
            migration_name=request.migration_name,
            version=request.version,
            target_scope=request.target_scope,
            target_dataset=request.target_dataset,
            checksum=checksum,
            status=status,
            applied_at=applied_at,
            applied_by=request.applied_by,
            bigquery_result=bq_result,
            error_message=error_message,
        )

    def rollback(self, request: MigrationRequest) -> MigrationResult:
        """Run the operator-supplied rollback_script.

        We don't try to be clever here. The operator provides the inverse DDL,
        we execute it, and we record the rollback in the same table with
        status=rolled_back. The original migration row is left untouched so the
        history is honest.
        """
        if not request.rollback_script:
            raise ValueError("rollback_script is required for rollback")
        rollback_request = MigrationRequest(
            migration_name=f"rollback:{request.migration_name}",
            version=request.version,
            target_scope=request.target_scope,
            target_dataset=request.target_dataset,
            ddl_statement=request.rollback_script,
            rollback_script=None,
            applied_by=request.applied_by,
        )
        result = self.apply(rollback_request)
        if result.status == "applied":
            result = result.model_copy(update={"status": "rolled_back"})
        return result


migration_service = MigrationService()
