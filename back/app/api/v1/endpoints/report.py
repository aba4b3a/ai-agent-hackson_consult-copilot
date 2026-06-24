from fastapi import APIRouter
from app.services.dashboard_service import dashboard_service

router = APIRouter()


@router.get('/{company_id}/report/weekly')
def get_weekly_report(company_id: str):
    return dashboard_service.get_weekly_report(company_id)
