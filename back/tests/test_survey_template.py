from fastapi.testclient import TestClient

from app.main import app


def test_initial_survey_is_loaded_from_storage_template():
    client = TestClient(app)

    res = client.get('/api/v1/companies/company_001/survey/initial')

    assert res.status_code == 200
    body = res.json()
    assert body['company_id'] == 'company_001'
    assert body['storage_path'] == 'survey_templates/common_initial_survey/v1/template.json'
    assert len(body['questions']) == 18
    assert body['questions'][0]['answer_type'] == 'long_text'
    assert body['questions'][4]['answer_type'] == 'single_choice'
    assert body['questions'][4]['choices'][0]['value'] == 'price'
