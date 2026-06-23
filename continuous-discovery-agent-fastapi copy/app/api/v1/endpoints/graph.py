from fastapi import APIRouter, Query
from app.schemas.bigquery import GraphQueryResponse
from app.services.bigquery_service import bigquery_service

router = APIRouter()


@router.get('/{company_id}/graph/query', response_model=GraphQueryResponse)
def get_graph_query(company_id: str, keyword: str | None = Query(default=None)):
    return bigquery_service.graph_query(company_id, keyword)
