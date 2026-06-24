from fastapi import APIRouter
from app.services.dashboard_service import dashboard_service

router = APIRouter()


@router.get('/{company_id}/knowledge/stats')
def get_knowledge_stats(company_id: str):
    return dashboard_service.get_knowledge_stats(company_id)
