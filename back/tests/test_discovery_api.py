from fastapi.testclient import TestClient

from app.main import app


def test_discovery_dashboard_flow() -> None:
    client = TestClient(app)

    workspaces = client.get("/api/workspaces")
    assert workspaces.status_code == 200
    workspace_id = workspaces.json()[0]["workspace_id"]

    dashboard = client.get(f"/api/workspaces/{workspace_id}/dashboard")
    assert dashboard.status_code == 200
    body = dashboard.json()
    assert body["metrics"]["sources_ingested"] >= 1
    assert "relationships_created" in body["metrics"]
    assert body["metrics"]["relationships_created"] >= 0
    assert body["signals"]


def test_report_submission_creates_searchable_evidence() -> None:
    client = TestClient(app)
    workspace_id = client.get("/api/workspaces").json()[0]["workspace_id"]
    form = client.post(
        "/api/report-forms",
        json={"workspace_id": workspace_id, "focus_topics": ["価格比較"]},
    ).json()

    response = client.post(
        "/api/report-submissions",
        json={
            "form_id": form["form_id"],
            "free_text": "駅前ドラッグと価格を比較する声が増えた",
            "customer_type": "高齢者",
            "product": "処方箋受付",
            "issue_category": "価格不安",
            "competitor": "駅前ドラッグ",
        },
    )

    assert response.status_code == 200
    evidence = client.get(f"/api/search/evidence?workspace_id={workspace_id}&q=駅前ドラッグ")
    assert evidence.status_code == 200
    assert evidence.json()["results"]
