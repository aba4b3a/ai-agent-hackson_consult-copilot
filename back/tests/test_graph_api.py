"""Graph API（design §10.4〜10.6）のテスト。DRY_RUN=true で seed フォールバック経路を検証する。"""
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

COMPANY = 'SMB-1042'


def _client(monkeypatch) -> TestClient:
    monkeypatch.setattr(settings, 'dry_run', True)
    return TestClient(app)


def test_slice_overview_without_center(monkeypatch):
    res = _client(monkeypatch).get(f'/api/v1/companies/{COMPANY}/graph/slice')

    assert res.status_code == 200
    body = res.json()
    assert body['nodes']
    assert body['meta']['center_node_id'] is None
    assert body['meta']['period'] == 'all'
    assert body['meta']['source'] == 'sample'
    node_ids = {n['node_id'] for n in body['nodes']}
    for edge in body['edges']:
        assert edge['source_node_id'] in node_ids
        assert edge['target_node_id'] in node_ids
        assert 'description' in edge  # UI の関係一覧カードが使う（§10.4）


def test_slice_limit_truncates_by_confidence(monkeypatch):
    res = _client(monkeypatch).get(f'/api/v1/companies/{COMPANY}/graph/slice', params={'limit': 3})

    assert res.status_code == 200
    body = res.json()
    assert len(body['nodes']) == 3
    assert body['meta']['truncated'] is True
    confidences = [n['confidence'] for n in body['nodes']]
    assert confidences == sorted(confidences, reverse=True)


def test_slice_types_filter(monkeypatch):
    res = _client(monkeypatch).get(f'/api/v1/companies/{COMPANY}/graph/slice', params={'types': 'KPI'})

    assert res.status_code == 200
    body = res.json()
    assert body['nodes']
    assert all(n['node_type'] == 'KPI' for n in body['nodes'])


def test_slice_around_center_keeps_center_and_neighbors(monkeypatch):
    client = _client(monkeypatch)
    overview = client.get(f'/api/v1/companies/{COMPANY}/graph/slice').json()
    center = overview['edges'][0]['source_node_id']

    res = client.get(
        f'/api/v1/companies/{COMPANY}/graph/slice',
        params={'center_node_id': center, 'depth': 1},
    )

    assert res.status_code == 200
    body = res.json()
    node_ids = {n['node_id'] for n in body['nodes']}
    assert center in node_ids
    assert body['meta']['center_node_id'] == center
    # depth=1 のスライスでは中心以外の全ノードが中心と隣接している
    for edge in body['edges']:
        assert edge['source_node_id'] in node_ids and edge['target_node_id'] in node_ids


def test_slice_unknown_center_returns_404(monkeypatch):
    res = _client(monkeypatch).get(
        f'/api/v1/companies/{COMPANY}/graph/slice',
        params={'center_node_id': 'node_does_not_exist'},
    )

    assert res.status_code == 404


def test_entities_search_matches_label(monkeypatch):
    client = _client(monkeypatch)
    overview = client.get(f'/api/v1/companies/{COMPANY}/graph/slice').json()
    label = overview['nodes'][0]['label']

    res = client.get(
        f'/api/v1/companies/{COMPANY}/graph/entities',
        params={'q': label[:2]},
    )

    assert res.status_code == 200
    hits = res.json()
    assert hits
    assert any(h['label'] == label for h in hits)


def test_entities_search_respects_types(monkeypatch):
    res = _client(monkeypatch).get(
        f'/api/v1/companies/{COMPANY}/graph/entities',
        params={'q': '率', 'types': 'KPI'},
    )

    assert res.status_code == 200
    assert all(h['node_type'] == 'KPI' for h in res.json())


def test_node_detail_returns_edges_and_evidence(monkeypatch):
    client = _client(monkeypatch)
    overview = client.get(f'/api/v1/companies/{COMPANY}/graph/slice').json()
    node_id = overview['edges'][0]['source_node_id']

    res = client.get(f'/api/v1/companies/{COMPANY}/graph/nodes/{node_id}')

    assert res.status_code == 200
    body = res.json()
    assert body['node_id'] == node_id
    assert body['adjacent_edges']
    assert body['evidence']
    assert body['evidence'][0]['response_id']
    assert body['evidence'][0]['raw_answer']


def test_node_detail_unknown_node_returns_404(monkeypatch):
    res = _client(monkeypatch).get(f'/api/v1/companies/{COMPANY}/graph/nodes/node_does_not_exist')

    assert res.status_code == 404
