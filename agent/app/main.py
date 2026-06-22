from fastapi import FastAPI

from agents.knowledge_agent import extract_knowledge
from app.schemas import ExtractionRequest, ExtractionResult

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
