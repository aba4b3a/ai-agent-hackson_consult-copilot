from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


MigrationScope = Literal["common", "tenant"]
MigrationStatus = Literal["pending", "applied", "failed", "rolled_back"]


class MigrationRequest(BaseModel):
    migration_name: str = Field(..., examples=["20260629_add_observation_signals"])
    version: str = Field(..., examples=["v1.3.0"])
    target_scope: MigrationScope
    target_dataset: str = Field(
        ..., description="BigQuery dataset id (without project prefix), e.g. cd_common or cd_tenant_acme"
    )
    ddl_statement: str
    rollback_script: str | None = None
    applied_by: str | None = None


class MigrationResult(BaseModel):
    migration_id: str
    migration_name: str
    version: str
    target_scope: MigrationScope
    target_dataset: str
    checksum: str
    status: MigrationStatus
    applied_at: str
    applied_by: str | None = None
    bigquery_result: dict[str, Any]
    error_message: str | None = None


class MigrationList(BaseModel):
    items: list[MigrationResult]
    total: int
