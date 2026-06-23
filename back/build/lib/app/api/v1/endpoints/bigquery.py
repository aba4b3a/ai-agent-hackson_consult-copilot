from fastapi import APIRouter
from app.schemas.bigquery import DdlResponse, ExecuteDdlResponse
from app.services.bigquery_service import bigquery_service

router = APIRouter()


@router.get('/{company_id}/bigquery/core-tables/ddl', response_model=DdlResponse)
def get_core_tables_ddl(company_id: str):
    return bigquery_service.generate_core_tables_ddl(company_id)


@router.post('/{company_id}/bigquery/core-tables', response_model=ExecuteDdlResponse)
def create_core_tables(company_id: str):
    return bigquery_service.create_core_tables(company_id)
