from fastapi.testclient import TestClient
from app.main import app


def test_prepare_onboarding():
    client = TestClient(app)
    res = client.post('/api/v1/companies/company_001/onboarding/prepare', json={'company_name': '田中美容室'})
    assert res.status_code == 200
    body = res.json()
    assert body['company_id'] == 'company_001'
    assert 'CREATE OR REPLACE PROPERTY GRAPH' in body['core_tables_ddl']
    assert len(body['initial_survey']['questions']) >= 8
