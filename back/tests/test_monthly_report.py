from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


def _previous_month_key() -> str:
    first_this_month = date.today().replace(day=1)
    previous_month = (first_this_month - timedelta(days=1)).replace(day=1)
    return previous_month.strftime('%Y-%m')


def test_monthly_report_is_created_in_storage_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, 'app_env', 'local')
    monkeypatch.setattr(settings, 'dry_run', True)
    monkeypatch.setattr(settings, 'wiki_bucket', '')
    monkeypatch.setattr(settings, 'storage_emulator_root', str(tmp_path))
    client = TestClient(app)

    res = client.get('/api/v1/companies/SMB-1042/report/monthly')

    assert res.status_code == 200
    body = res.json()
    period_key = _previous_month_key()
    storage_path = f'tenants/SMB-1042/reports/monthly/{period_key}/report.json'
    stored_file = tmp_path / 'local-cd-agent-knowledge' / storage_path
    assert body['monthly']['source'] == 'generated_and_saved'
    assert body['monthly']['storagePath'] == storage_path
    assert stored_file.exists()
    assert body['metrics'][0]['label'] == 'Observed facts'
    assert body['charts']
    assert body['sections']


def test_monthly_report_prefers_existing_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, 'app_env', 'local')
    monkeypatch.setattr(settings, 'dry_run', True)
    monkeypatch.setattr(settings, 'wiki_bucket', '')
    monkeypatch.setattr(settings, 'storage_emulator_root', str(tmp_path))
    client = TestClient(app)

    first = client.get('/api/v1/companies/SMB-1042/report/monthly')
    second = client.get('/api/v1/companies/SMB-1042/report/monthly')

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()['monthly']['source'] == 'cloud_storage'
