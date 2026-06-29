from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.migration import MigrationList, MigrationRequest, MigrationResult
from app.services.migration_service import migration_service

router = APIRouter()


@router.post("/apply", response_model=MigrationResult)
def apply_migration(request: MigrationRequest):
    return migration_service.apply(request)


@router.post("/rollback", response_model=MigrationResult)
def rollback_migration(request: MigrationRequest):
    try:
        return migration_service.rollback(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("", response_model=MigrationList)
def list_migrations(
    target_dataset: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
):
    return migration_service.list(target_dataset=target_dataset, limit=limit)
