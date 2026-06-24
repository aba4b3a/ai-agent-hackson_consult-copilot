from fastapi import APIRouter
from app.api.v1.endpoints import (
    bigquery, companies, copilot, custom_tables, dashboard,
    graph, graph_nodes, health, knowledge_stats, report, survey, wiki,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=['health'])
api_router.include_router(companies.router, prefix='/companies', tags=['companies'])
api_router.include_router(bigquery.router, prefix='/companies', tags=['bigquery'])
api_router.include_router(survey.router, prefix='/companies', tags=['survey'])
api_router.include_router(graph.router, prefix='/companies', tags=['graph'])
api_router.include_router(graph_nodes.router, prefix='/companies', tags=['graph'])
api_router.include_router(custom_tables.router, prefix='/companies', tags=['custom-tables'])
api_router.include_router(wiki.router, prefix='/companies', tags=['wiki'])
api_router.include_router(dashboard.router, prefix='/companies', tags=['dashboard'])
api_router.include_router(knowledge_stats.router, prefix='/companies', tags=['knowledge'])
api_router.include_router(report.router, prefix='/companies', tags=['report'])
api_router.include_router(copilot.router, prefix='/companies', tags=['copilot'])
