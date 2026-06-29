from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.db.firestore import firestore_repo
from app.schemas.approval import (
    ApprovalApplyResult,
    ApprovalCreate,
    ApprovalDecision,
    ApprovalRecord,
    ApprovalStatus,
)

COLLECTION = "pending_approvals"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(target_type: str) -> str:
    return f"appr_{target_type}_{uuid.uuid4().hex[:12]}"


class ApprovalService:
    def create(self, data: ApprovalCreate) -> ApprovalRecord:
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
            created_at=_now_iso(),
        )
        firestore_repo.set(COLLECTION, record.approval_id, record.model_dump())
        return record

    def list(
        self,
        company_id: str,
        status: ApprovalStatus | None = None,
        limit: int | None = 100,
    ) -> list[ApprovalRecord]:
        filters: dict[str, Any] = {"company_id": company_id}
        if status is not None:
            filters["status"] = status
        rows = firestore_repo.query(
            COLLECTION,
            filters=filters,
            order_by="created_at",
            descending=True,
            limit=limit,
        )
        return [ApprovalRecord(**row) for row in rows]

    def get(self, approval_id: str) -> ApprovalRecord | None:
        row = firestore_repo.get(COLLECTION, approval_id)
        if row is None:
            return None
        return ApprovalRecord(**row)

    def _transition(
        self,
        approval_id: str,
        next_status: ApprovalStatus,
        decision: ApprovalDecision,
    ) -> ApprovalRecord:
        existing = self.get(approval_id)
        if existing is None:
            raise KeyError(approval_id)
        if existing.status != "pending":
            raise ValueError(
                f"approval {approval_id} is not pending (current status={existing.status})"
            )
        patch = {
            "status": next_status,
            "decided_by": decision.decided_by,
            "decided_at": _now_iso(),
            "decision_note": decision.decision_note,
        }
        updated = firestore_repo.update(COLLECTION, approval_id, patch)
        return ApprovalRecord(**updated)

    def approve(self, approval_id: str, decision: ApprovalDecision) -> ApprovalRecord:
        return self._transition(approval_id, "approved", decision)

    def reject(self, approval_id: str, decision: ApprovalDecision) -> ApprovalRecord:
        return self._transition(approval_id, "rejected", decision)

    def mark_applied(self, approval_id: str, applied_result: dict[str, Any]) -> ApprovalApplyResult:
        existing = self.get(approval_id)
        if existing is None:
            raise KeyError(approval_id)
        if existing.status != "approved":
            raise ValueError(
                f"approval {approval_id} must be approved before apply (current status={existing.status})"
            )
        patch = {
            "status": "applied",
            "applied_at": _now_iso(),
            "applied_result": applied_result,
        }
        updated = firestore_repo.update(COLLECTION, approval_id, patch)
        record = ApprovalRecord(**updated)
        return ApprovalApplyResult(
            approval_id=record.approval_id,
            status=record.status,
            applied_result=record.applied_result or {},
        )


approval_service = ApprovalService()
