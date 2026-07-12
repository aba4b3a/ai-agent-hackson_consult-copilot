from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from app.schemas.bigquery import GraphQueryResponse
from app.schemas.graph import GraphEntity, GraphSliceResponse, NodeDetailResponse
from app.services.bigquery_service import bigquery_service
from app.services.graph_service import graph_service

router = APIRouter()

Period = Literal['last_7_days', 'last_30_days', 'last_90_days', 'all']


@router.get('/{company_id}/graph/slice', response_model=GraphSliceResponse)
def get_graph_slice(
    company_id: str,
    center_node_id: str | None = Query(default=None),
    depth: int = Query(default=1, ge=1, le=2),
    limit: int = Query(default=50, ge=1, le=100),
    types: str | None = Query(default=None, description='node_type の CSV（例 Signal,KPI）'),
    period: Period = Query(default='all'),
):
    result = graph_service.get_slice(company_id, center_node_id, depth, limit, types, period)
    if result is None:
        raise HTTPException(status_code=404, detail=f'node not found: {center_node_id}')
    return result


@router.get('/{company_id}/graph/entities', response_model=list[GraphEntity])
def search_graph_entities(
    company_id: str,
    q: str = Query(min_length=1, description='label / description の部分一致（大文字小文字無視）'),
    types: str | None = Query(default=None, description='node_type の CSV'),
    limit: int = Query(default=20, ge=1, le=100),
):
    return graph_service.search_entities(company_id, q, types, limit)


@router.get('/{company_id}/graph/nodes/{node_id}', response_model=NodeDetailResponse)
def get_graph_node_detail(company_id: str, node_id: str):
    result = graph_service.get_node_detail(company_id, node_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f'node not found: {node_id}')
    return result


@router.get('/{company_id}/graph/query', response_model=GraphQueryResponse)
def get_graph_query(
    company_id: str,
    keyword: str | None = Query(default=None),
    node_type: str | None = Query(default=None, description='起点ノードの node_type（例: Signal, KPI）'),
    target_type: str | None = Query(default=None, description='終点ノードの node_type'),
    edge_type: str | None = Query(default=None, description='edge_type（例: LEADING_INDICATOR_OF）'),
    hops: int = Query(default=1, ge=1, le=3),
):
    return bigquery_service.graph_query(
        company_id, keyword=keyword, node_type=node_type, target_type=target_type,
        edge_type=edge_type, hops=hops,
    )
