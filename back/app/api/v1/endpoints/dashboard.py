from fastapi import APIRouter
from app.services.dashboard_service import dashboard_service

router = APIRouter()


@router.get('/{company_id}/dashboard')
def get_dashboard(company_id: str):
    return dashboard_service.get_dashboard(company_id)
