"""intake ルール抽出の語彙統一（design §10.1/10.2）と簡易名寄せのテスト。"""
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.schemas.survey import SurveyResponseRecord
from app.services.knowledge_service import knowledge_service

NODE_VOCAB = {
    'CompanyProfile', 'CustomerSegment', 'KPI', 'Process', 'ProductService',
    'ResearchPolicy', 'Signal', 'TacitKnowledge', 'Person', 'Risk',
}
EDGE_VOCAB = {'CREATES', 'DRIVES', 'KNOWS', 'LEADING_INDICATOR_OF', 'OBSERVES', 'PRESSURES', 'PROTECTS'}


def _response(text: str, numeric_value: float | None = None) -> SurveyResponseRecord:
    return SurveyResponseRecord(
        response_id='resp_test_001',
        company_id='SMB-TEST',
        question_id='q01',
        respondent_role='現場担当',
        collected_at='2026-07-09T00:00:00Z',
        survey_frequency='ad_hoc',
        question_text='現場の状況を教えてください。',
        answer_type='long_text',
        raw_answer=text,
        numeric_value=numeric_value,
        answer_json={},
        qualitative_summary=text[:300],
        quantitative_summary=None,
        related_node_ids=[],
        related_edge_ids=[],
    )


def test_extraction_uses_design_vocabulary_only(monkeypatch):
    monkeypatch.setattr(settings, 'dry_run', True)
    text = 'ベテランの田中さんの判断で売上を守っています。最近は退職のリスクが懸念です。'

    nodes, edges = knowledge_service.extract_from_response('SMB-TEST', _response(text))

    node_types = {n.node_type for n in nodes}
    assert node_types <= NODE_VOCAB
    assert 'Question' not in node_types
    assert 'Skill' not in node_types
    assert {'TacitKnowledge', 'KPI', 'Risk', 'Person'} <= node_types
    assert {e.edge_type for e in edges} <= EDGE_VOCAB
    assert all(e.edge_type != 'RELATED_TO' for e in edges)


def test_extraction_edge_rules_and_confidence(monkeypatch):
    monkeypatch.setattr(settings, 'dry_run', True)
    text = 'ベテランの田中さんの判断で売上を守っています。最近は退職のリスクが懸念です。'

    nodes, edges = knowledge_service.extract_from_response('SMB-TEST', _response(text))

    edge_types = {e.edge_type for e in edges}
    assert 'KNOWS' in edge_types  # Person -> TacitKnowledge
    assert 'PROTECTS' in edge_types  # TacitKnowledge -> KPI
    assert 'PRESSURES' in edge_types  # Risk -> KPI
    assert all(n.confidence < 1.0 for n in nodes)
    hypothesis_flags = {e.edge_type: e.properties.get('hypothesis') for e in edges}
    assert hypothesis_flags.get('PROTECTS') is False


def test_extraction_label_comes_from_answer(monkeypatch):
    monkeypatch.setattr(settings, 'dry_run', True)
    text = '検査工程の不満が増えて売上への変化が心配です。'

    nodes, _ = knowledge_service.extract_from_response('SMB-TEST', _response(text))

    signal = next(n for n in nodes if n.node_type == 'Signal')
    assert signal.label != '顧客・現場の兆候'
    assert signal.label in text


def test_signal_leading_indicator_hypothesis(monkeypatch):
    monkeypatch.setattr(settings, 'dry_run', True)
    text = 'クレームが増えていて、リピートに影響しそうです。'

    nodes, edges = knowledge_service.extract_from_response('SMB-TEST', _response(text))

    li = [e for e in edges if e.edge_type == 'LEADING_INDICATOR_OF']
    assert li, 'Signal->KPI の LEADING_INDICATOR_OF が生成されること'
    assert li[0].properties.get('hypothesis') is True


def test_name_matching_connects_to_existing_node(monkeypatch):
    monkeypatch.setattr(settings, 'dry_run', True)
    existing = [{'node_id': 'node_kpi_quote_margin', 'node_type': 'KPI', 'label': '見積粗利率'}]
    monkeypatch.setattr(knowledge_service, '_match_existing_nodes', lambda company_id, text: existing)
    text = '見積粗利率が下がりそうなクレームの変化があります。売上も心配です。'

    nodes, edges = knowledge_service.extract_from_response('SMB-TEST', _response(text))

    # 既存 KPI に一致したので新規 KPI ノードは作らない
    assert not [n for n in nodes if n.node_type == 'KPI']
    # 抽出 Signal から既存 KPI ノードへエッジが張られる（島の接続）
    targets = {e.target_node_id for e in edges if e.edge_type == 'LEADING_INDICATOR_OF'}
    assert 'node_kpi_quote_margin' in targets


def test_intake_submission_end_to_end(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, 'dry_run', True)
    monkeypatch.setattr(settings, 'wiki_bucket', '')
    monkeypatch.setattr(settings, 'storage_emulator_root', str(tmp_path))
    client = TestClient(app)

    res = client.post(
        '/api/v1/companies/SMB-1042/survey/initial/submissions',
        json={
            'respondent_role': '代表取締役',
            'answers': [{
                'question_id': 'initial_v1_q01',
                'question_text': '御社の主な事業内容を教えてください。',
                'answer_type': 'long_text',
                'respondent_role': '代表取締役',
                'raw_answer': 'ベテランの佐藤さんの経験で品質を守り、売上を伸ばしています。',
                'numeric_value': None,
                'answer_json': {},
            }],
            'chat_transcript': [],
        },
    )

    assert res.status_code == 200
    body = res.json()
    for result in body['response_results']:
        for node in result['extracted_nodes']:
            assert node['node_type'] in NODE_VOCAB
        for edge in result['extracted_edges']:
            assert edge['edge_type'] in EDGE_VOCAB
