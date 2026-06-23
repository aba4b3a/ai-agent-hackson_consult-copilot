from fastapi import APIRouter
from app.api.v1.endpoints import bigquery, companies, custom_tables, graph, health, survey, wiki

api_router = APIRouter()
api_router.include_router(health.router, tags=['health'])
api_router.include_router(companies.router, prefix='/companies', tags=['companies'])
api_router.include_router(bigquery.router, prefix='/companies', tags=['bigquery'])
api_router.include_router(survey.router, prefix='/companies', tags=['survey'])
api_router.include_router(graph.router, prefix='/companies', tags=['graph'])
api_router.include_router(custom_tables.router, prefix='/companies', tags=['custom-tables'])
api_router.include_router(wiki.router, prefix='/companies', tags=['wiki'])
