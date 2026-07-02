from fastapi import FastAPI

from agents.copilot_agent import answer_question
from agents.followup_agent import generate_followups
from agents.knowledge_agent import extract_knowledge
from app.schemas import (
    CopilotAnswerRequest,
    CopilotAnswerResult,
    ExtractionRequest,
    ExtractionResult,
    FollowupRequest,
    FollowupResponse,
)

app = FastAPI(
    title="Continuous Discovery Agent Runtime",
    version="0.1.0",
)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/knowledge/extract", response_model=ExtractionResult)
def knowledge_extract(request: ExtractionRequest) -> ExtractionResult:
    return extract_knowledge(request)


@app.post("/v1/intake/followups", response_model=FollowupResponse)
def intake_followups(request: FollowupRequest) -> FollowupResponse:
    return generate_followups(request)


@app.post("/v1/copilot/answer", response_model=CopilotAnswerResult)
def copilot_answer(request: CopilotAnswerRequest) -> CopilotAnswerResult:
    return answer_question(request)
