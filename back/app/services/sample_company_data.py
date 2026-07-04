from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SampleCompanyData:
    default_company_id = 'SMB-1042'

    def __init__(self) -> None:
        self.seed_root = Path(__file__).resolve().parents[1] / 'storage_seed' / 'companies'

    def _company_root(self, company_id: str) -> Path | None:
        safe_company_id = company_id.replace('\\', '/').strip('/').replace('..', '_')
        direct = self.seed_root / safe_company_id
        if direct.exists():
            return direct
        if safe_company_id in {'demo', 'local-demo', 'sample'}:
            fallback = self.seed_root / self.default_company_id
            return fallback if fallback.exists() else None
        return None

    def has_company(self, company_id: str) -> bool:
        return self._company_root(company_id) is not None

    def structured(self, company_id: str) -> dict[str, Any] | None:
        root = self._company_root(company_id)
        if not root:
            return None
        path = root / 'structured_knowledge.json'
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding='utf-8'))

    def wiki_files(self, company_id: str) -> list[dict[str, Any]]:
        root = self._company_root(company_id)
        if not root:
            return []
        wiki_root = root / 'wiki' / 'current'
        if not wiki_root.exists():
            return []
        results: list[dict[str, Any]] = []
        for path in sorted(wiki_root.rglob('*')):
            if not path.is_file():
                continue
            rel = path.relative_to(wiki_root)
            results.append(
                {
                    'bucket': 'sample-seed',
                    'path': f'tenants/{company_id}/wiki/current/{str(rel).replace("\\", "/")}',
                    'size': path.stat().st_size,
                    'updated': path.stat().st_mtime,
                    'generation': None,
                }
            )
        return results

    def read_wiki_file(self, company_id: str, relative_path: str) -> str | None:
        root = self._company_root(company_id)
        if not root:
            return None
        safe_relative = relative_path.lstrip('/').replace('..', '_').replace('\\', '/')
        path = root / 'wiki' / 'current' / safe_relative
        if not path.exists() or not path.is_file():
            return None
        return path.read_text(encoding='utf-8')

    def dashboard(self, company_id: str) -> dict[str, Any] | None:
        data = self.structured(company_id)
        if not data:
            return None
        nodes = data.get('knowledge_nodes', [])
        signals = [n for n in nodes if n.get('node_type') == 'Signal']
        company = data.get('company', {})
        insights = [
            {
                'id': node.get('node_id', f'sig-{index}'),
                'title': node.get('label', 'Signal'),
                'description': node.get('description', '')[:90],
                'meta': f"confidence: {round(float(node.get('confidence', 0)) * 100)}%",
                'priority': 'danger' if '競合' in node.get('label', '') else 'neutral',
            }
            for index, node in enumerate(signals[:4])
        ]
        return {
            'consultant': {
                'name': '佐藤 里奈',
                'subtitle': f"{company.get('company_name', company_id)} / {company.get('consulting_theme', '組織学習支援')}",
                'isLive': True,
            },
            'hero': {
                'title': '今週の重要発見',
                'count': len(signals),
                'summary': '価格再確認と競合価格言及が、見積成約率と見積粗利率の先行シグナルになっています。',
            },
            'insights': insights,
            'portfolio': [
                {'id': company_id, 'name': company.get('company_name', company_id), 'status': company.get('segment', 'sample company')},
                {'id': 'SMB-2198', 'name': '青葉フーズ', 'status': '未接続 / サンプル切替候補'},
                {'id': 'SMB-3307', 'name': 'みなとケア', 'status': '未接続 / サンプル切替候補'},
            ],
            'nextActions': [
                {'id': 'act-1', 'title': '価格再確認の週次質問を確認', 'description': '営業担当に価格再確認回数、商品、競合名を聞く。'},
                {'id': 'act-2', 'title': '見積粗利率の承認判断', 'description': 'KPI候補を人間承認し、current_kpi_definitions へ反映する。'},
            ],
        }

    def knowledge_stats(self, company_id: str) -> dict[str, Any] | None:
        data = self.structured(company_id)
        if not data:
            return None
        nodes = data.get('knowledge_nodes', [])
        edges = data.get('knowledge_edges', [])
        responses = data.get('survey_responses', [])
        type_counts: dict[str, int] = {}
        for node in nodes:
            node_type = node.get('node_type', 'Unknown')
            type_counts[node_type] = type_counts.get(node_type, 0) + 1
        tone_map = {'CompanyProfile': 'blue', 'KPI': 'yellow', 'Signal': 'green', 'TacitKnowledge': 'purple'}
        accumulation = [
            {'id': f'acc-{node_type}', 'label': node_type, 'value': count, 'tone': tone_map.get(node_type, 'blue')}
            for node_type, count in list(type_counts.items())[:4]
        ]
        return {
            'header': {
                'title': 'Knowledge Formation',
                'subtitle': 'LLM Wiki と BigQuery seed に基づくサンプル企業ナレッジ',
                'statusLabel': 'Seeded Knowledge Asset',
                'statusDescription': '北斗精密工業のKPI候補・重点管理指標候補を読込済み',
            },
            'health': {
                'score': 78,
                'title': 'Knowledge Health',
                'signals': [
                    f"Nodes: {len(nodes)}",
                    f"Edges: {len(edges)}",
                    f"Responses: {len(responses)}",
                ],
            },
            'accumulation': accumulation,
            'pipeline': [
                {'id': 'p1', 'label': 'Survey responses', 'value': len(responses), 'tone': 'blue'},
                {'id': 'p2', 'label': 'KPI candidates', 'value': len(data.get('kpi_candidates', [])), 'tone': 'teal'},
                {'id': 'p3', 'label': 'Focus metrics', 'value': len(data.get('focus_metric_candidates', [])), 'tone': 'amber'},
            ],
            'gap': {
                'title': 'Knowledge Gaps',
                'description': '小ロット案件の粗利基準と価格再確認回数の閾値は、承認前の未確定情報です。',
                'tags': [
                    {'id': 'gap-1', 'label': 'gross margin baseline', 'tone': 'rose'},
                    {'id': 'gap-2', 'label': 'price signal threshold', 'tone': 'blue'},
                ],
            },
            'recentKnowledge': [
                f"{node.get('node_type')}: {node.get('label')}"
                for node in nodes[-5:]
            ],
        }

    def graph_nodes(self, company_id: str) -> dict[str, Any] | None:
        data = self.structured(company_id)
        if not data:
            return None
        nodes = data.get('knowledge_nodes', [])
        edges = data.get('knowledge_edges', [])
        tone_map = {'Signal': 'rose', 'KPI': 'amber', 'TacitKnowledge': 'violet', 'CompanyProfile': 'cyan', 'ResearchPolicy': 'blue'}
        positions = ['center', 'topLeft', 'topRight', 'bottomLeft', 'bottomRight']
        display_nodes = [
            {
                'id': node.get('node_id'),
                'label': str(node.get('label', 'node'))[:8],
                'tone': tone_map.get(node.get('node_type'), 'blue'),
                'position': positions[index % len(positions)],
            }
            for index, node in enumerate(nodes[:5])
        ]
        top_edge = edges[0] if edges else {}
        return {
            'header': {'title': 'Knowledge Graph', 'subtitle': 'BigQuery Graph seed による関係可視化'},
            'filters': ['全て', '価格', '競合', 'KPI因果', '暗黙知'],
            'map': {
                'title': 'KPI Signal Map',
                'nodes': display_nodes,
                'stats': f"Nodes {len(nodes)} / Relations {len(edges)}",
            },
            'views': [
                {'id': 'v1', 'label': 'Signal', 'tone': 'yellow'},
                {'id': 'v2', 'label': 'KPI', 'tone': 'green'},
                {'id': 'v3', 'label': 'Tacit', 'tone': 'purple'},
                {'id': 'v4', 'label': 'Policy', 'tone': 'blue'},
            ],
            'relation': {
                'title': 'Selected relation',
                'segment': top_edge.get('edge_type', 'LEADING_INDICATOR_OF'),
                'evidence': top_edge.get('description', '価格再確認回数とKPI候補の関係を観測します。'),
                'customers': 'A社 / 小ロット案件',
                'hypothesis': '価格再確認が増えると見積成約率が下がる可能性があります。',
                'confidence': int(float(top_edge.get('confidence', 0.78)) * 100),
            },
            'lens': [
                {'id': 'l1', 'label': 'Fact graph', 'value': '回答イベントから確認済みの顧客発言と見積状況'},
                {'id': 'l2', 'label': 'Hypothesis graph', 'value': '価格再確認と成約率低下の仮説'},
                {'id': 'l3', 'label': 'Gap graph', 'value': '粗利基準と閾値は未承認'},
                {'id': 'l4', 'label': 'KPI graph', 'value': '見積粗利率・見積成約率との関連'},
            ],
        }

    def weekly_report(self, company_id: str) -> dict[str, Any] | None:
        data = self.structured(company_id)
        if not data:
            return None
        signals = [n for n in data.get('knowledge_nodes', []) if n.get('node_type') in {'Signal', 'KPI'}]
        tacit = [n for n in data.get('knowledge_nodes', []) if n.get('node_type') == 'TacitKnowledge']
        highlights = [
            {
                'id': node.get('node_id', f'h-{index}'),
                'kind': 'FACT' if node.get('node_type') == 'Signal' else 'HYPOTHESIS',
                'tone': 'green' if node.get('node_type') == 'Signal' else 'yellow',
                'title': node.get('label', ''),
                'description': node.get('description', '')[:90],
                'meta': node.get('node_type', ''),
            }
            for index, node in enumerate((signals + tacit)[:5])
        ]
        return {
            'header': {'title': 'Report Copilot', 'subtitle': '事実と仮説を分けてコンサルに提示'},
            'weekly': {
                'title': 'Weekly Discovery',
                'period': f'{company_id} / 2026-07-01 - 2026-07-04',
                'summary': '価格再確認2回、競合価格言及1件。見積成約率と見積粗利率の重点観測が必要です。',
            },
            'highlights': highlights,
            'snippets': [
                'A社の小ロット案件で価格の再確認が2回発生。',
                '「他社見積と合わせたい」という競合比較の発言あり。',
                'ベテランの見積調整判断が粗利確保に寄与する可能性。',
            ],
            'recommendation': {
                'title': 'Recommended observation',
                'description': '営業担当へ週次で価格再確認、競合名、対象商品、値引き要求有無を確認してください。',
                'actionLabel': 'Research Agentに質問を登録',
            },
            'ctaLabel': 'Generate report',
        }

    def copilot_answer(self, company_id: str, message: str) -> str | None:
        data = self.structured(company_id)
        if not data:
            return None
        kpis = ', '.join(item.get('kpi_name', '') for item in data.get('kpi_candidates', []))
        focus_metrics = ', '.join(item.get('metric_name', '') for item in data.get('focus_metric_candidates', []))
        return (
            'サンプルデータに基づく回答です。\n\n'
            f'- 参照企業: {data.get("company", {}).get("company_name", company_id)}\n'
            f'- LLM Wiki: company_profile.md / kpi_definitions.yaml / focus_metrics.yaml / research_policy.yaml を参照対象にしています。\n'
            f'- BigQuery seed: onboarding_answer_events、kpi_candidates、focus_metric_candidates、knowledge_nodes、knowledge_edges 相当の構造化データを参照しています。\n'
            f'- KPI候補: {kpis}\n'
            f'- 重点管理指標候補: {focus_metrics}\n\n'
            '現時点では「価格再確認回数」と「競合価格言及」を先行指標として見積成約率・見積粗利率を観測するのが妥当です。'
            'ただし正式採用と current 定義への反映は人間承認待ちとして扱ってください。'
        )


sample_company_data = SampleCompanyData()
