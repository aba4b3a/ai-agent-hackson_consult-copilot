"""初期ヒアリング「AIに補足する」チャット(/survey/initial/assist)のテスト。"""
from fastapi.testclient import TestClient

from app.main import app
from app.services import intake_assist_service as intake_assist_module

_REQUEST_BODY = {
    'question_id': 'initial_v1_q01',
    'question_text': '御社の主な事業内容を教えてください。',
    'purpose': '事業構造の把握',
    'current_answer': '地元向けの美容室です。',
    'chat_history': [
        {'role': 'assistant', 'text': '具体例、頻度、関係する商品・顧客層が分かれば追加で教えてください。'},
    ],
    'user_message': '常連のお客様がほとんどです。',
}


def test_intake_assist_returns_agent_reply(monkeypatch):
    captured = {}

    async def fake_run_agent_turn(user_id, session_id, message, timeout_seconds=None):
        captured['user_id'] = user_id
        captured['session_id'] = session_id
        captured['message'] = message
        return 'FOLLOWUP: ありがとうございます。常連のお客様は、どんなきっかけで通い始める方が多いですか？'

    monkeypatch.setattr(intake_assist_module.agent_client, 'run_agent_turn', fake_run_agent_turn)
    client = TestClient(app)

    res = client.post('/api/v1/companies/SMB-1042/survey/initial/assist', json=_REQUEST_BODY)

    assert res.status_code == 200
    body = res.json()
    assert body['company_id'] == 'SMB-1042'
    assert body['question_id'] == 'initial_v1_q01'
    # マーカーは除去されてUIに渡る
    assert body['reply'].startswith('ありがとうございます')
    assert body['mode'] == 'followup'
    assert body['answer_draft'] is None
    # 会話の材料がプロンプトに含まれ、質問ごとのセッションに分かれること
    assert captured['user_id'] == 'SMB-1042'
    assert 'initial_v1_q01' in captured['session_id']
    assert 'FOLLOWUP:' in captured['message']
    assert '御社の主な事業内容' in captured['message']
    assert '地元向けの美容室です。' in captured['message']
    assert '常連のお客様がほとんどです。' in captured['message']


def _history(user_count: int) -> list[dict]:
    """assistant開始の交互履歴で、ユーザー発言が user_count 件の履歴を作る。"""
    history = [{'role': 'assistant', 'text': '補足があれば教えてください。'}]
    for i in range(user_count):
        history.append({'role': 'user', 'text': f'補足その{i + 1}です。'})
        history.append({'role': 'assistant', 'text': f'質問その{i + 1}です。'})
    return history


def test_intake_assist_switches_to_summary_on_third_user_message(monkeypatch):
    captured = {}

    async def fake_run_agent_turn(user_id, session_id, message, timeout_seconds=None):
        captured['message'] = message
        return 'SUMMARY: 地元の常連客向けの美容室で、売上の8割が常連です。新規は月に数人程度です。'

    monkeypatch.setattr(intake_assist_module.agent_client, 'run_agent_turn', fake_run_agent_turn)
    client = TestClient(app)

    # 履歴にユーザー発言2件 + 今回で3通目 → まとめモード
    body = {**_REQUEST_BODY, 'chat_history': _history(2)}
    res = client.post('/api/v1/companies/SMB-1042/survey/initial/assist', json=body)

    assert res.status_code == 200
    payload = res.json()
    assert payload['mode'] == 'summary'
    assert payload['answer_draft'].startswith('地元の常連客向けの美容室')
    assert payload['reply'] == payload['answer_draft']
    # プロンプトがまとめ指示に切り替わっていること
    assert 'SUMMARY:' in captured['message']
    assert 'そのまま貼れる' in captured['message']


def test_intake_assist_stays_followup_before_third_message(monkeypatch):
    captured = {}

    async def fake_run_agent_turn(user_id, session_id, message, timeout_seconds=None):
        captured['message'] = message
        return 'FOLLOWUP: なるほど。それはいつ頃からですか？'

    monkeypatch.setattr(intake_assist_module.agent_client, 'run_agent_turn', fake_run_agent_turn)
    client = TestClient(app)

    # 履歴にユーザー発言1件 + 今回で2通目 → まだ深掘りモード
    body = {**_REQUEST_BODY, 'chat_history': _history(1)}
    res = client.post('/api/v1/companies/SMB-1042/survey/initial/assist', json=body)

    assert res.json()['mode'] == 'followup'
    assert 'FOLLOWUP:' in captured['message']
    assert 'まとめ' not in captured['message'].split('## 応答ルール')[1].splitlines()[2]


def test_intake_assist_summary_marker_violation_falls_back_to_followup(monkeypatch):
    async def fake_run_agent_turn(user_id, session_id, message, timeout_seconds=None):
        # まとめ期待なのにマーカー無しで返してきたケース
        return 'これまでの内容をまとめると、常連中心の美容室とのことですね。'

    monkeypatch.setattr(intake_assist_module.agent_client, 'run_agent_turn', fake_run_agent_turn)
    client = TestClient(app)

    body = {**_REQUEST_BODY, 'chat_history': _history(2)}
    res = client.post('/api/v1/companies/SMB-1042/survey/initial/assist', json=body)

    payload = res.json()
    # 誤った本文をワンタップで回答欄に入れさせない（安全側に倒す）
    assert payload['mode'] == 'followup'
    assert payload['answer_draft'] is None
    assert payload['reply'].startswith('これまでの内容')


def test_intake_assist_falls_back_when_agent_unavailable(monkeypatch):
    async def fake_run_agent_turn(user_id, session_id, message, timeout_seconds=None):
        raise RuntimeError('All connection attempts failed')

    monkeypatch.setattr(intake_assist_module.agent_client, 'run_agent_turn', fake_run_agent_turn)
    client = TestClient(app)

    res = client.post('/api/v1/companies/SMB-1042/survey/initial/assist', json=_REQUEST_BODY)

    assert res.status_code == 200
    assert 'うまく応答できませんでした' in res.json()['reply']


def test_intake_assist_falls_back_on_empty_reply(monkeypatch):
    async def fake_run_agent_turn(user_id, session_id, message, timeout_seconds=None):
        return ''

    monkeypatch.setattr(intake_assist_module.agent_client, 'run_agent_turn', fake_run_agent_turn)
    client = TestClient(app)

    res = client.post('/api/v1/companies/SMB-1042/survey/initial/assist', json=_REQUEST_BODY)

    assert res.status_code == 200
    assert 'うまく応答できませんでした' in res.json()['reply']
