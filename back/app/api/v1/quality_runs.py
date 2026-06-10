from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class QualityRunCreateRequest(BaseModel):
    pull_request_url: str
    commit_sha: str


class QualityRunCreateResponse(BaseModel):
    quality_run_id: str
    status: str


@router.post("")
def create_quality_run(request: QualityRunCreateRequest) -> QualityRunCreateResponse:
    return QualityRunCreateResponse(
        quality_run_id=f"qr-{request.commit_sha[:8]}",
        status="created",
    )


@router.get("/{quality_run_id}")
def get_quality_run(quality_run_id: str) -> dict[str, object]:
    return {
        "quality_run_id": quality_run_id,
        "quality_score": 82,
        "release_decision": "conditional_go",
        "risk_level": "medium",
    }
