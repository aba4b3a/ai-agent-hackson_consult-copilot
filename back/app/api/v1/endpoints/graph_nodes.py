from fastapi import APIRouter
from app.services.dashboard_service import dashboard_service

router = APIRouter()


@router.get('/{company_id}/graph/nodes')
def get_graph_nodes(company_id: str):
    return dashboard_service.get_graph_nodes(company_id)
