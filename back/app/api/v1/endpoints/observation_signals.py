from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.observation_signal import (
    ObservationSignalBatch,
    ObservationSignalWriteResult,
)
from app.services.observation_signal_service import observation_signal_service

router = APIRouter()


@router.post(
    "/{company_id}/observation-signals",
    response_model=ObservationSignalWriteResult,
)
def insert_observation_signals(company_id: str, batch: ObservationSignalBatch):
    if batch.company_id != company_id:
        raise HTTPException(
            status_code=400,
            detail=f"company_id mismatch: path={company_id} body={batch.company_id}",
        )
    return observation_signal_service.insert_batch(batch)
