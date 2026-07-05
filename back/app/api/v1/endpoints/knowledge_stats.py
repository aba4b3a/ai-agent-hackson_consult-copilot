from fastapi import APIRouter
from app.services.dashboard_service import dashboard_service

router = APIRouter()


@router.get('/{company_id}/knowledge/stats')
def get_knowledge_stats(company_id: str):
    return dashboard_service.get_knowledge_stats(company_id)


@router.get('/{company_id}/knowledge/kpi-trends')
def get_kpi_trends(company_id: str):
    return dashboard_service.get_kpi_trends(company_id)
