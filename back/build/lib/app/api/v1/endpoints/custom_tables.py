from fastapi import APIRouter
from app.schemas.knowledge import CustomTableProposal, CustomTableRequest
from app.services.knowledge_service import knowledge_service

router = APIRouter()


@router.post('/{company_id}/custom-tables/propose', response_model=CustomTableProposal)
def propose_custom_table(company_id: str, data: CustomTableRequest):
    return knowledge_service.propose_custom_table(company_id, data.table_id, data.purpose, data.columns)
