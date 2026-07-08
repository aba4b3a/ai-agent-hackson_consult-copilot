from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.research import (
    Assignment,
    AssignmentCreate,
    AssignmentList,
    AssignmentStatus,
    FollowupAnswerResult,
    FollowupAnswerSubmit,
    FollowupQuestionCreate,
)
from app.services.research_service import research_service

router = APIRouter()


@router.post("/{company_id}/research/followup-questions")
def register_followup_question(company_id: str, data: FollowupQuestionCreate):
    if data.company_id != company_id:
        raise HTTPException(
            status_code=400,
            detail=f"company_id mismatch: path={company_id} body={data.company_id}",
        )
    return research_service.register_followup_question(data)


@router.post("/{company_id}/research/assignments", response_model=Assignment)
def create_assignment(company_id: str, data: AssignmentCreate):
    if data.company_id != company_id:
        raise HTTPException(
            status_code=400,
            detail=f"company_id mismatch: path={company_id} body={data.company_id}",
        )
    return research_service.assign(data)


@router.get("/{company_id}/research/assignments", response_model=AssignmentList)
def list_assignments(
    company_id: str,
    target_role: str | None = Query(default=None),
    status: AssignmentStatus | None = Query(default="open"),
    limit: int = Query(default=200, ge=1, le=500),
):
    base = research_service.list_assignments(
        company_id, target_role=target_role, status=status, limit=limit
    )
    # Enrich each assignment with its question text/category so the UI can
    # render the question without an extra round-trip.
    enriched = []
    for item in base.items:
        enriched_item = item.model_dump()
        # Schedule-driven (sched_*) items are resolved live from GCS and
        # already carry their display fields — skip the BigQuery question
        # join, which would just overwrite them with nulls.
        if not item.assignment_id.startswith("sched_"):
            question = research_service.get_question(company_id, item.followup_question_id) or {}
            enriched_item["question_text"] = question.get("question_text")
            enriched_item["question_category"] = question.get("question_category")
            enriched_item["reason"] = question.get("reason")
            enriched_item["expected_answer_format"] = question.get("expected_answer_format")
            enriched_item["target_candidate_table"] = question.get("target_candidate_table")
            enriched_item["target_candidate_id"] = question.get("target_candidate_id")
            enriched_item["target_candidate_name"] = question.get("target_candidate_name")
        enriched.append(enriched_item)
    payload = base.model_dump()
    payload["items"] = enriched
    return payload


@router.post("/{company_id}/research/answers", response_model=FollowupAnswerResult)
def submit_followup_answer(company_id: str, data: FollowupAnswerSubmit):
    try:
        return research_service.submit_answer(company_id, data)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"assignment {data.assignment_id} not found")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/{company_id}/research/tick")
def trigger_research_tick(company_id: str, cohort: str = Query(default="manual")):
    """Manual fan-out trigger. In production this is also called from the
    Pub/Sub push subscription bound to consult-copilot-research-dispatch-tick.
    """
    return research_service.tick(company_id, cohort=cohort)
