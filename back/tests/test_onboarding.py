from fastapi.testclient import TestClient
from app.core.config import settings
from app.main import app
from app.schemas.survey import SurveyAnswerCreate
from app.services.onboarding_service import (
    _answers_payload,
    _build_stage1_message,
    _build_stage2_message,
    onboarding_service,
)


def test_prepare_onboarding():
    client = TestClient(app)
    res = client.post('/api/v1/companies/company_001/onboarding/prepare', json={'company_name': '田中美容室'})
    assert res.status_code == 200
    body = res.json()
    assert body['company_id'] == 'company_001'
    assert 'CREATE OR REPLACE PROPERTY GRAPH' in body['core_tables_ddl']
    assert len(body['initial_survey']['questions']) >= 8


def _answer(response_id: str | None = None) -> SurveyAnswerCreate:
    return SurveyAnswerCreate(
        question_id='initial_v1_q01',
        question_text='御社の主な事業内容を教えてください。',
        answer_type='long_text',
        respondent_role='owner',
        raw_answer='地元の常連客向けの美容室です。',
        response_id=response_id,
    )


def test_stage1_message_instructs_graph_extraction():
    message = _build_stage1_message('SMB-1042', '田中美容室', _answers_payload([_answer('resp_abc123')]))

    assert 'list_knowledge_nodes' in message
    assert 'upsert_knowledge_nodes' in message
    assert 'upsert_knowledge_edges' in message
    assert 'source_response_id' in message
    # 回答ペイロードに response_id が同梱され、エージェントが証拠参照に使える
    assert 'resp_abc123' in message


def test_stage2_message_instructs_graph_refresh():
    message = _build_stage2_message('SMB-1042', '田中美容室', _answers_payload([_answer('resp_abc123')]), [])

    assert 'list_knowledge_nodes' in message
    assert 'upsert_knowledge_nodes' in message
    assert 'resp_abc123' in message


def test_submission_passes_response_ids_to_agent(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, 'dry_run', True)
    monkeypatch.setattr(settings, 'wiki_bucket', '')
    monkeypatch.setattr(settings, 'storage_emulator_root', str(tmp_path))
    captured = {}

    async def fake_run_agent_onboarding(company_id, answers):
        captured['company_id'] = company_id
        captured['answers'] = answers

    monkeypatch.setattr(onboarding_service, 'run_agent_onboarding', fake_run_agent_onboarding)
    client = TestClient(app)

    res = client.post(
        '/api/v1/companies/SMB-1042/survey/initial/submissions',
        json={
            'respondent_role': 'owner',
            'answers': [{
                'question_id': 'initial_v1_q01',
                'question_text': '御社の主な事業内容を教えてください。',
                'answer_type': 'long_text',
                'respondent_role': 'owner',
                'raw_answer': '地元の常連客向けの美容室です。',
                'numeric_value': None,
                'answer_json': {},
            }],
            'chat_transcript': [],
        },
    )

    assert res.status_code == 200
    assert captured['company_id'] == 'SMB-1042'
    response_id = captured['answers'][0].response_id
    assert response_id and response_id.startswith('resp_')
    # 提出レスポンス側の response_id と一致していること
    body = res.json()
    assert body['response_results'][0]['response']['response_id'] == response_id
