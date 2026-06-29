from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.approval import (
    ApprovalApplyResult,
    ApprovalCreate,
    ApprovalDecision,
    ApprovalList,
    ApprovalRecord,
    ApprovalStatus,
)
from app.services.approval_service import approval_service

router = APIRouter()


@router.post("/{company_id}/approvals", response_model=ApprovalRecord)
def create_approval(company_id: str, data: ApprovalCreate):
    if data.company_id != company_id:
        raise HTTPException(
            status_code=400,
            detail=f"company_id mismatch: path={company_id} body={data.company_id}",
        )
    return approval_service.create(data)


@router.get("/{company_id}/approvals", response_model=ApprovalList)
def list_approvals(
    company_id: str,
    status: ApprovalStatus | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
):
    items = approval_service.list(company_id, status=status, limit=limit)
    return ApprovalList(
        company_id=company_id,
        items=items,
        total=len(items),
        status_filter=status,
    )


@router.get("/{company_id}/approvals/{approval_id}", response_model=ApprovalRecord)
def get_approval(company_id: str, approval_id: str):
    record = approval_service.get(approval_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"approval {approval_id} not found")
    if record.company_id != company_id:
        raise HTTPException(status_code=404, detail="approval does not belong to this company")
    return record


@router.post("/{company_id}/approvals/{approval_id}/approve", response_model=ApprovalRecord)
def approve_approval(company_id: str, approval_id: str, decision: ApprovalDecision):
    record = approval_service.get(approval_id)
    if record is None or record.company_id != company_id:
        raise HTTPException(status_code=404, detail=f"approval {approval_id} not found")
    try:
        return approval_service.approve(approval_id, decision)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/{company_id}/approvals/{approval_id}/reject", response_model=ApprovalRecord)
def reject_approval(company_id: str, approval_id: str, decision: ApprovalDecision):
    record = approval_service.get(approval_id)
    if record is None or record.company_id != company_id:
        raise HTTPException(status_code=404, detail=f"approval {approval_id} not found")
    try:
        return approval_service.reject(approval_id, decision)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post(
    "/{company_id}/approvals/{approval_id}/applied",
    response_model=ApprovalApplyResult,
)
def mark_approval_applied(company_id: str, approval_id: str, applied_result: dict):
    record = approval_service.get(approval_id)
    if record is None or record.company_id != company_id:
        raise HTTPException(status_code=404, detail=f"approval {approval_id} not found")
    try:
        return approval_service.mark_applied(approval_id, applied_result)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
