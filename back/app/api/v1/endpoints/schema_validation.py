from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.schema_validation_service import (
    validate_knowledge_output,
    validate_research_output,
)


router = APIRouter()


class ValidationRequest(BaseModel):
    payload: dict


class ValidationResult(BaseModel):
    schema_name: Literal["knowledge_agent_output", "research_agent_output"]
    valid: bool
    errors: list[str]


@router.post("/knowledge-agent-output", response_model=ValidationResult)
def validate_knowledge(request: ValidationRequest) -> ValidationResult:
    errors = validate_knowledge_output(request.payload)
    return ValidationResult(schema_name="knowledge_agent_output", valid=not errors, errors=errors)


@router.post("/research-agent-output", response_model=ValidationResult)
def validate_research(request: ValidationRequest) -> ValidationResult:
    errors = validate_research_output(request.payload)
    return ValidationResult(schema_name="research_agent_output", valid=not errors, errors=errors)
