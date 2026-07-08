"""Dashboard / Knowledge / Graph / WeeklyReport をBigQueryから集計して返すサービス。
DRY_RUN=true or BQ接続失敗時はフォールバックデータを返す。"""
from __future__ import annotations
from datetime import date, datetime, timedelta

from app.core.config import settings
from app.crud.storage_crud import storage_crud
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


def _previous_month(today: date | None = None) -> tuple[date, date, str]:
    current = today or date.today()
    first_this_month = current.replace(day=1)
    last_previous_month = first_this_month - timedelta(days=1)
    first_previous_month = last_previous_month.replace(day=1)
    return first_previous_month, first_this_month, first_previous_month.strftime("%Y-%m")


def _average_confidence(rows: list[dict]) -> int:
    values = [float(row.get("confidence") or 0) for row in rows]
    if not values:
        return 0
    return round(sum(values) / len(values) * 100)


class DashboardService:
    # ── Dashboard (Discovery Feed) ──────────────────────────────────────
    def get_dashboard(self, company_id: str) -> dict:
        knowledge_nodes = settings.qualified_table(company_id, 'knowledge_nodes')
        sample_dashboard = sample_company_data.dashboard(company_id)

        node_rows = _query(f"""
            SELECT node_type, COUNT(*) AS cnt
            FROM `{knowledge_nodes}`
            WHERE status = 'active'
            GROUP BY node_type ORDER BY cnt DESC LIMIT 10
        """)
        signal_rows = _query(f"""
            SELECT node_type, label, description, confidence
            FROM `{knowledge_nodes}`
            WHERE node_type IN ('Signal','Risk') AND status = 'active'
            ORDER BY confidence DESC LIMIT 5
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
                {"id": "a2", "title": "月次レポートを確認", "description": f"/api/v1/companies/{company_id}/report/monthly を参照"},
            ],
        }

    # ── Knowledge Stats ─────────────────────────────────────────────────
    def get_knowledge_stats(self, company_id: str) -> dict:
        knowledge_nodes = settings.qualified_table(company_id, 'knowledge_nodes')
        knowledge_edges = settings.qualified_table(company_id, 'knowledge_edges')
        survey_responses = settings.qualified_table(company_id, 'survey_responses')
        sample_stats = sample_company_data.knowledge_stats(company_id)

        type_rows = _query(f"""
            SELECT node_type, COUNT(*) AS cnt
            FROM `{knowledge_nodes}` WHERE status='active'
            GROUP BY node_type
        """)
        edge_rows = _query(f"""
            SELECT COUNT(*) AS cnt FROM `{knowledge_edges}`
        """)
        resp_rows = _query(f"""
            SELECT COUNT(*) AS cnt FROM `{survey_responses}`
        """)
        recent_rows = _query(f"""
            SELECT label, node_type FROM `{knowledge_nodes}`
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
        knowledge_nodes = settings.qualified_table(company_id, 'knowledge_nodes')
        knowledge_edges = settings.qualified_table(company_id, 'knowledge_edges')
        sample_graph = sample_company_data.graph_nodes(company_id)

        node_rows = _query(f"""
            SELECT node_id, node_type, label, confidence
            FROM `{knowledge_nodes}`
            WHERE status='active' ORDER BY confidence DESC LIMIT 20
        """)
        edge_rows = _query(f"""
            SELECT source_node_id, target_node_id, edge_type, strength
            FROM `{knowledge_edges}`
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
        knowledge_nodes = settings.qualified_table(company_id, 'knowledge_nodes')
        sample_report = sample_company_data.weekly_report(company_id)

        signal_rows = _query(f"""
            SELECT node_type, label, description, confidence, created_at
            FROM `{knowledge_nodes}`
            WHERE node_type IN ('Signal','Risk','KPI')
              AND created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
            ORDER BY confidence DESC LIMIT 10
        """)
        tacit_rows = _query(f"""
            SELECT label, description, confidence
            FROM `{knowledge_nodes}`
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

    # ── Monthly Report ───────────────────────────────────────────────────
    def get_monthly_report(self, company_id: str) -> dict:
        start, end, period_key = _previous_month()
        storage_path = f"tenants/{company_id}/reports/monthly/{period_key}/report.json"

        if storage_crud.exists(storage_path):
            report = storage_crud.read_json(storage_path)
            report.setdefault("monthly", {})["source"] = "cloud_storage"
            report["monthly"]["storagePath"] = storage_path
            return report

        report = self._build_monthly_report(company_id, start, end, period_key)
        try:
            storage_result = storage_crud.upload_json(storage_path, report)
            report["monthly"]["source"] = "generated_and_saved"
            report["monthly"]["storagePath"] = storage_result.get("path", storage_path)
            report["monthly"]["gsUri"] = storage_result.get("gs_uri")
        except Exception:
            report["monthly"]["source"] = "generated_unsaved"
            report["monthly"]["storagePath"] = storage_path
        return report

    def _build_monthly_report(self, company_id: str, start: date, end: date, period_key: str) -> dict:
        dataset = settings.dataset_id(company_id)
        project = settings.project_id
        sample_report = sample_company_data.monthly_report(company_id, period_key)

        signal_rows = _query(f"""
            SELECT node_type, label, description, confidence, created_at
            FROM `{project}.{dataset}.knowledge_nodes`
            WHERE node_type IN ('Signal','Risk','KPI')
              AND DATE(created_at) >= DATE('{start.isoformat()}')
              AND DATE(created_at) < DATE('{end.isoformat()}')
            ORDER BY confidence DESC LIMIT 12
        """)
        tacit_rows = _query(f"""
            SELECT node_type, label, description, confidence, created_at
            FROM `{project}.{dataset}.knowledge_nodes`
            WHERE node_type = 'TacitKnowledge'
              AND DATE(created_at) >= DATE('{start.isoformat()}')
              AND DATE(created_at) < DATE('{end.isoformat()}')
            ORDER BY confidence DESC LIMIT 8
        """)
        response_rows = _query(f"""
            SELECT raw_answer, numeric_value, collected_at
            FROM `{project}.{dataset}.survey_responses`
            WHERE DATE(collected_at) >= DATE('{start.isoformat()}')
              AND DATE(collected_at) < DATE('{end.isoformat()}')
            ORDER BY collected_at DESC LIMIT 50
        """)

        if not signal_rows and not tacit_rows and not response_rows and sample_report:
            return sample_report

        fact_count = len(signal_rows)
        hypothesis_count = len(tacit_rows)
        evidence_count = len(response_rows)
        confidence = _average_confidence(signal_rows + tacit_rows)
        top_rows = signal_rows[:3] + tacit_rows[:2]
        highlights = [
            {
                "id": f"monthly-{index}",
                "kind": "FACT" if row.get("node_type") in {"Signal", "Risk", "KPI"} else "HYPOTHESIS",
                "tone": "green" if row.get("node_type") in {"Signal", "Risk", "KPI"} else "yellow",
                "title": row.get("label") or "Untitled insight",
                "description": (row.get("description") or "")[:100],
                "meta": row.get("node_type") or f"confidence {round(float(row.get('confidence') or 0) * 100)}%",
            }
            for index, row in enumerate(top_rows)
        ] or [{
            "id": "monthly-empty",
            "kind": "FACT",
            "tone": "green",
            "title": "前月の観測データはまだ不足しています",
            "description": "日報、ヒアリング、KPIファイルが蓄積されると月次レポートに反映されます。",
            "meta": "data gap",
        }]

        snippets = [
            (row.get("raw_answer") or "")[:120]
            for row in response_rows[:4]
            if row.get("raw_answer")
        ] or [row["title"] for row in highlights[:3]]
        summary = (
            f"{period_key} は事実 {fact_count} 件、仮説 {hypothesis_count} 件、"
            f"根拠候補 {evidence_count} 件を確認しました。"
        )

        return {
            "header": {"title": "Monthly Discovery Report", "subtitle": "Cloud Storageに保存された前月レポート"},
            "monthly": {
                "title": f"{period_key} 月次レポート",
                "period": f"{company_id} / {start.isoformat()} - {(end - timedelta(days=1)).isoformat()}",
                "summary": summary,
                "generatedAt": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                "source": "generated",
                "storagePath": f"tenants/{company_id}/reports/monthly/{period_key}/report.json",
            },
            "metrics": [
                {"id": "facts", "label": "Observed facts", "value": fact_count, "unit": "件", "tone": "green"},
                {"id": "hypotheses", "label": "Hypotheses", "value": hypothesis_count, "unit": "件", "tone": "yellow"},
                {"id": "evidence", "label": "Evidence", "value": evidence_count, "unit": "件", "tone": "blue"},
                {"id": "confidence", "label": "Avg. confidence", "value": confidence, "unit": "%", "tone": "slate"},
            ],
            "charts": [
                {"id": "facts", "label": "事実", "value": fact_count, "unit": "件", "tone": "green"},
                {"id": "hypotheses", "label": "仮説", "value": hypothesis_count, "unit": "件", "tone": "yellow"},
                {"id": "evidence", "label": "根拠", "value": evidence_count, "unit": "件", "tone": "blue"},
            ],
            "sections": [
                {
                    "id": "executive-summary",
                    "title": "Executive summary",
                    "body": summary,
                    "kind": "summary",
                },
                {
                    "id": "interpretation",
                    "title": "Consultant interpretation",
                    "body": "仮説は確定原因として扱わず、次月の観測テーマで追加検証してください。",
                    "kind": "hypothesis",
                },
            ],
            "highlights": highlights,
            "snippets": snippets,
            "recommendation": {
                "title": "Next month observation",
                "description": "高信頼の事実と未検証の仮説を分け、現場質問とKPI観測を継続してください。",
                "actionLabel": "Research Agentに質問を登録",
            },
            "ctaLabel": "Regenerate report",
        }


dashboard_service = DashboardService()
