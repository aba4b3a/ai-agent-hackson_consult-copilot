from __future__ import annotations

from datetime import datetime, timezone

from app.core.config import settings
from app.crud.bigquery_crud import bigquery_crud
from app.schemas.observation_signal import (
    ObservationSignalBatch,
    ObservationSignalWriteResult,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ObservationSignalService:
    def insert_batch(self, batch: ObservationSignalBatch) -> ObservationSignalWriteResult:
        table = settings.qualified_table(batch.company_id, "observation_signals")
        now = _now_iso()
        rows = []
        for item in batch.items:
            payload = item.model_dump()
            payload.update(
                {
                    "approval_status": "proposed",
                    "approved_by": None,
                    "approved_at": None,
                    "created_at": now,
                    "updated_at": now,
                }
            )
            rows.append(payload)
        bq_result = bigquery_crud.insert_json_rows(table, rows)
        return ObservationSignalWriteResult(
            company_id=batch.company_id,
            inserted_count=len(rows),
            bigquery_write_result=bq_result,
        )


observation_signal_service = ObservationSignalService()
