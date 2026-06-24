from fastapi import APIRouter
from pydantic import BaseModel
from app.services.copilot_service import copilot_service

router = APIRouter()


class CopilotRequest(BaseModel):
    message: str
    session_id: str | None = None


@router.post('/{company_id}/report/copilot')
async def chat_copilot(company_id: str, data: CopilotRequest):
    return await copilot_service.chat(company_id, data.message, data.session_id)
