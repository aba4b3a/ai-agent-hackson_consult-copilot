"""Dashboard / Knowledge / Graph / WeeklyReport をBigQueryから集計して返すサービス。
DRY_RUN=true or BQ接続失敗時はフォールバックデータを返す。"""
from __future__ import annotations
from app.core.config import settings
from app.crud.bigquery_crud import bigquery_crud
from app.services.sample_company_data import sample_company_data


def _query(sql: str) -> list[dict]:
    if settings.dry_run:
        return []
    try:
        from app.db.bigquery import get_bigquery_client
        client = get_bigquery_client()
        return [dict(row) for row in client.query(sql).result()]
    except Exception:
        return []


class DashboardService:
    # ── Dashboard (Discovery Feed) ──────────────────────────────────────
    def get_dashboard(self, company_id: str) -> dict:
        dataset = settings.dataset_id(company_id)
        project = settings.project_id
        sample_dashboard = sample_company_data.dashboard(company_id)

        node_rows = _query(f"""
            SELECT node_type, COUNT(*) AS cnt
            FROM `{project}.{dataset}.knowledge_nodes`
            WHERE status = 'active'
            GROUP BY node_type ORDER BY cnt DESC LIMIT 10
        """)
        signal_rows = _query(f"""
            SELECT node_type, label, description, confidence
            FROM `{project}.{dataset}.knowledge_nodes`
            WHERE node_type IN ('Signal','Risk') AND status = 'active'
            ORDER BY confidence DESC LIMIT 5
        """)
        recent_rows = _query(f"""
            SELECT label, node_type, confidence
            FROM `{project}.{dataset}.knowledge_nodes`
            WHERE status = 'active'
            ORDER BY created_at DESC LIMIT 3
        """)

        total_nodes = sum(r["cnt"] for r in node_rows)
        if total_nodes == 0 and sample_dashboard:
            return sample_dashboard
        insights = [
            {
                "id": f"sig-{i}",
                "title": r["label"],
                "description": r["description"][:80] if r.get("description") else r["node_type"],
                "meta": f"confidence: {round(r['confidence'] * 100)}%",
                "priority": "danger" if r["node_type"] == "Risk" else "neutral",
            }
            for i, r in enumerate(signal_rows)
        ] or [
            {"id": "sig-0", "title": "データ収集中", "description": "アンケートを送信するとインサイトが表示されます", "meta": "", "priority": "neutral"}
        ]

        return {
            "consultant": {"name": "Consultant", "subtitle": f"{total_nodes} knowledge nodes", "isLive": True},
            "hero": {
                "title": "今週の重要発見",
                "count": len(signal_rows) or 0,
                "summary": "  /  ".join(f"{r['node_type']} {r['cnt']}" for r in node_rows[:3]) or "データ収集中",
            },
            "insights": insights,
            "portfolio": [{"id": company_id, "name": company_id, "status": f"{total_nodes} nodes"}],
            "nextActions": [
                {"id": "a1", "title": "アンケートを送信", "description": f"/api/v1/companies/{company_id}/survey/initial から質問を取得できます"},
                {"id": "a2", "title": "週次レポートを確認", "description": f"/api/v1/companies/{company_id}/report/weekly を参照"},
            ],
        }

    # ── Knowledge Stats ─────────────────────────────────────────────────
    def get_knowledge_stats(self, company_id: str) -> dict:
        dataset = settings.dataset_id(company_id)
        project = settings.project_id
        sample_stats = sample_company_data.knowledge_stats(company_id)

        type_rows = _query(f"""
            SELECT node_type, COUNT(*) AS cnt
            FROM `{project}.{dataset}.knowledge_nodes` WHERE status='active'
            GROUP BY node_type
        """)
        edge_rows = _query(f"""
            SELECT COUNT(*) AS cnt FROM `{project}.{dataset}.knowledge_edges`
        """)
        resp_rows = _query(f"""
            SELECT COUNT(*) AS cnt FROM `{project}.{dataset}.survey_responses`
        """)
        recent_rows = _query(f"""
            SELECT label, node_type FROM `{project}.{dataset}.knowledge_nodes`
            WHERE status='active' ORDER BY created_at DESC LIMIT 5
        """)

        type_map = {r["node_type"]: r["cnt"] for r in type_rows}
        total_nodes = sum(type_map.values())
        if total_nodes == 0 and sample_stats:
            return sample_stats
        total_edges = edge_rows[0]["cnt"] if edge_rows else 0
        total_responses = resp_rows[0]["cnt"] if resp_rows else 0
        score = min(100, int((total_nodes / max(1, total_nodes + 5)) * 100))

        tone_map = {"TacitKnowledge": "purple", "KPI": "yellow", "Signal": "green", "Person": "blue"}
        accumulation = [
            {"id": f"acc-{i}", "label": node_type, "value": cnt,
             "tone": tone_map.get(node_type, "blue")}
            for i, (node_type, cnt) in enumerate(list(type_map.items())[:4])
        ] or [{"id": "acc-0", "label": "Q&A", "value": total_responses, "tone": "blue"}]

        return {
            "header": {
                "title": "Knowledge Formation",
                "subtitle": "ナレッジの形成・集約状況",
                "statusLabel": "Knowledge Asset",
                "statusDescription": "Formation status",
            },
            "health": {
                "score": score,
                "title": "Knowledge Health",
                "signals": [
                    f"Nodes: {total_nodes}",
                    f"Edges: {total_edges}",
                    f"Responses: {total_responses}",
                ],
            },
            "accumulation": accumulation,
            "pipeline": [
                {"id": "p1", "label": "Survey responses", "value": total_responses, "tone": "blue"},
                {"id": "p2", "label": "Knowledge nodes", "value": total_nodes, "tone": "teal"},
                {"id": "p3", "label": "Relationships", "value": total_edges, "tone": "amber"},
            ],
            "gap": {
                "title": "Knowledge Gaps",
                "description": "アンケートを続けることでナレッジが充実します" if total_nodes < 10 else "ナレッジ形成が進んでいます",
                "tags": [{"id": "g1", "label": "ask field", "tone": "blue"}],
            },
            "recentKnowledge": [f"{r['node_type']}: {r['label']}" for r in recent_rows] or ["データなし"],
        }

    # ── Graph Nodes ─────────────────────────────────────────────────────
    def get_graph_nodes(self, company_id: str) -> dict:
        dataset = settings.dataset_id(company_id)
        project = settings.project_id
        sample_graph = sample_company_data.graph_nodes(company_id)

        node_rows = _query(f"""
            SELECT node_id, node_type, label, confidence
            FROM `{project}.{dataset}.knowledge_nodes`
            WHERE status='active' ORDER BY confidence DESC LIMIT 20
        """)
        edge_rows = _query(f"""
            SELECT source_node_id, target_node_id, edge_type, strength
            FROM `{project}.{dataset}.knowledge_edges`
            ORDER BY strength DESC LIMIT 30
        """)
        total_nodes = len(node_rows)
        total_edges = len(edge_rows)
        if total_nodes == 0 and sample_graph:
            return sample_graph

        tone_map = {"Signal": "rose", "KPI": "amber", "TacitKnowledge": "violet", "Person": "cyan"}
        positions = ["topLeft", "topRight", "bottomLeft", "bottomRight", "center"]
        nodes_for_display = [
            {
                "id": r["node_id"],
                "label": r["label"][:8],
                "tone": tone_map.get(r["node_type"], "blue"),
                "position": positions[i % len(positions)],
                "nodeType": r["node_type"],
                "value": None,
                "unit": None,
            }
            for i, r in enumerate(node_rows[:5])
        ] or [{"id": "n0", "label": "データなし", "tone": "blue", "position": "center"}]

        return {
            "header": {"title": "Knowledge Graph", "subtitle": "関係を見える化"},
            "filters": ["全て", "顧客・課題", "競合影響", "KPI因果", "仮説"],
            "map": {
                "title": "Segment Issue Map",
                "nodes": nodes_for_display,
                "stats": f"Nodes {total_nodes} / Relations {total_edges}",
            },
            "views": [
                {"id": "v1", "label": "Issue", "tone": "blue"},
                {"id": "v2", "label": "KPI", "tone": "green"},
                {"id": "v3", "label": "Signal", "tone": "yellow"},
                {"id": "v4", "label": "Person", "tone": "purple"},
            ],
            "relation": {
                "title": "Selected relation",
                "segment": edge_rows[0]["edge_type"] if edge_rows else "データなし",
                "evidence": f"Relations: {total_edges}",
                "customers": "",
                "hypothesis": "",
                "confidence": int((edge_rows[0].get("strength") or 0.5) * 100) if edge_rows else 50,
            },
            "lens": [
                {"id": "l1", "label": "Fact graph", "value": "観測された関係"},
                {"id": "l2", "label": "Hypothesis graph", "value": "可能性の関係"},
                {"id": "l3", "label": "Gap graph", "value": "足りない証拠"},
                {"id": "l4", "label": "KPI graph", "value": "指標との関連"},
            ],
        }

    # ── KPI Trends ───────────────────────────────────────────────────────
    def get_kpi_trends(self, company_id: str) -> dict:
        return {"items": sample_company_data.kpi_trends(company_id) or []}

    # ── Weekly Report ────────────────────────────────────────────────────
    def get_weekly_report(self, company_id: str) -> dict:
        dataset = settings.dataset_id(company_id)
        project = settings.project_id
        sample_report = sample_company_data.weekly_report(company_id)

        signal_rows = _query(f"""
            SELECT node_type, label, description, confidence, created_at
            FROM `{project}.{dataset}.knowledge_nodes`
            WHERE node_type IN ('Signal','Risk','KPI')
              AND created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
            ORDER BY confidence DESC LIMIT 10
        """)
        tacit_rows = _query(f"""
            SELECT label, description, confidence
            FROM `{project}.{dataset}.knowledge_nodes`
            WHERE node_type = 'TacitKnowledge'
              AND created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
            ORDER BY confidence DESC LIMIT 5
        """)
        total_this_week = len(signal_rows) + len(tacit_rows)
        if total_this_week == 0 and sample_report:
            return sample_report

        highlights = []
        for i, r in enumerate(signal_rows[:3]):
            highlights.append({
                "id": f"fact-{i}",
                "kind": "FACT",
                "tone": "green",
                "title": r["label"],
                "description": (r.get("description") or "")[:80],
                "meta": r["node_type"],
            })
        for i, r in enumerate(tacit_rows[:2]):
            highlights.append({
                "id": f"hyp-{i}",
                "kind": "HYPOTHESIS",
                "tone": "yellow",
                "title": r["label"],
                "description": (r.get("description") or "")[:80],
                "meta": f"confidence {round(r['confidence'] * 100)}%",
            })

        if not highlights:
            highlights = [{
                "id": "empty",
                "kind": "FACT",
                "tone": "green",
                "title": "今週のデータなし",
                "description": "アンケート回答が蓄積されるとレポートが生成されます",
                "meta": "",
            }]

        return {
            "header": {"title": "Report Copilot", "subtitle": "事実と仮説を分けてコンサルに提示"},
            "weekly": {
                "title": "Weekly Discovery",
                "period": f"{company_id} / 直近7日",
                "summary": f"{len(signal_rows)} facts / {len(tacit_rows)} hypotheses / {total_this_week} total",
            },
            "highlights": highlights,
            "snippets": [r["label"] for r in (signal_rows + tacit_rows)[:3]] or ["データ収集中"],
            "recommendation": {
                "title": "Recommended observation",
                "description": "引き続きアンケートを送信して知識を蓄積してください",
                "actionLabel": "send intake",
            },
            "ctaLabel": "Generate report",
        }


dashboard_service = DashboardService()
