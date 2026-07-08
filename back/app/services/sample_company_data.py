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
            rel = path.relative_to(wiki_root).as_posix()
            results.append(
                {
                    'bucket': 'sample-seed',
                    'path': f'tenants/{company_id}/wiki/current/{rel}',
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
        ui = data.get('ui', {})
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
                'summary': ui.get('dashboard_summary', '重点管理指標の変化がKPI候補の先行シグナルになっています。'),
            },
            'insights': insights,
            'portfolio': [
                {'id': company_id, 'name': company.get('company_name', company_id), 'status': company.get('segment', 'sample company')},
                *[
                    candidate
                    for candidate in (
                        {'id': 'SMB-2198', 'name': '青葉ベーカリー&カフェ', 'status': '飲食・小売 / サンプル切替候補'},
                        {'id': 'SMB-3307', 'name': 'みなとケア', 'status': '未接続 / サンプル切替候補'},
                    )
                    if candidate['id'] != company_id
                ],
            ],
            'nextActions': ui.get('next_actions') or [
                {'id': 'act-1', 'title': '週次質問を確認', 'description': '重点管理指標の変化と背景を現場担当に聞く。'},
                {'id': 'act-2', 'title': 'KPI候補の承認判断', 'description': 'KPI候補を人間承認し、current_kpi_definitions へ反映する。'},
            ],
        }

    def knowledge_stats(self, company_id: str) -> dict[str, Any] | None:
        data = self.structured(company_id)
        if not data:
            return None
        ui = data.get('ui', {})
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
                'subtitle': '企業属性情報および過去傾向データに基づく企業ナレッジ',
                'statusLabel': 'Seeded Knowledge Asset',
                'statusDescription': ui.get('knowledge_status', f"{data.get('company', {}).get('company_name', company_id)} のKPI候補・重点管理指標候補を読込済み"),
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
                'description': ui.get('gap_description', 'KPI候補と重点管理指標候補の一部は、承認前の未確定情報です。'),
                'tags': ui.get('gap_tags') or [
                    {'id': 'gap-1', 'label': 'gross margin baseline', 'tone': 'rose'},
                    {'id': 'gap-2', 'label': 'signal threshold', 'tone': 'blue'},
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
        ui = data.get('ui', {})
        nodes = data.get('knowledge_nodes', [])
        edges = data.get('knowledge_edges', [])
        tone_map = {
            'Signal': 'rose',
            'KPI': 'amber',
            'TacitKnowledge': 'violet',
            'CompanyProfile': 'cyan',
            'ResearchPolicy': 'blue',
            'CustomerSegment': 'cyan',
            'ProductService': 'violet',
            'Process': 'blue',
        }
        edge_tone_map = {
            'LEADING_INDICATOR_OF': 'rose',
            'PRESSURES': 'rose',
            'PROTECTS': 'violet',
            'MEASURES': 'amber',
            'INFORMS': 'blue',
            'DRIVES': 'blue',
            'CREATES': 'amber',
            'OBSERVES': 'blue',
            'AFFECTS': 'slate',
        }
        positions = ['center', 'topLeft', 'topRight', 'bottomLeft', 'bottomRight']
        layout_points = [
            (180, 130),
            (72, 54),
            (178, 36),
            (288, 58),
            (52, 134),
            (306, 132),
            (86, 212),
            (180, 222),
            (284, 210),
            (128, 88),
            (232, 92),
            (180, 174),
            (118, 166),
            (244, 166),
        ]
        size_map = {'CompanyProfile': 'lg', 'KPI': 'md', 'Signal': 'md', 'ResearchPolicy': 'lg'}
        display_nodes = [
            {
                'id': node.get('node_id'),
                'label': str(node.get('label', 'node'))[:14],
                'tone': tone_map.get(node.get('node_type'), 'blue'),
                'position': positions[index % len(positions)],
                'nodeType': node.get('node_type', 'Unknown'),
                'description': node.get('description', ''),
                'x': layout_points[index % len(layout_points)][0],
                'y': layout_points[index % len(layout_points)][1],
                'size': size_map.get(node.get('node_type'), 'sm'),
                'meta': node.get('node_type', 'Unknown'),
                'value': node.get('properties', {}).get('latest_value'),
                'unit': node.get('properties', {}).get('unit'),
            }
            for index, node in enumerate(nodes[:14])
        ]
        node_ids = {node['id'] for node in display_nodes}
        display_edges = [
            {
                'id': edge.get('edge_id', f'edge-{index}'),
                'source': edge.get('source_node_id'),
                'target': edge.get('target_node_id'),
                'label': edge.get('edge_type', 'RELATED_TO'),
                'tone': edge_tone_map.get(edge.get('edge_type'), 'slate'),
                'strength': max(0.2, min(1.0, float(edge.get('strength') or edge.get('confidence') or 0.55))),
                'description': edge.get('description', ''),
            }
            for index, edge in enumerate(edges)
            if edge.get('source_node_id') in node_ids and edge.get('target_node_id') in node_ids
        ][:18]
        top_edge = edges[0] if edges else {}
        return {
            'header': {'title': 'Knowledge Graph', 'subtitle': 'BigQuery Graph seed による関係可視化'},
            'filters': ui.get('graph_filters') or ['全て', '価格', '競合', 'KPI因果', '暗黙知'],
            'map': {
                'title': ui.get('graph_title', 'KPI Signal Map'),
                'nodes': display_nodes,
                'edges': display_edges,
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
                'evidence': top_edge.get('description', '重点管理指標とKPI候補の関係を観測します。'),
                'customers': ui.get('graph_customers', ''),
                'hypothesis': ui.get('graph_hypothesis', '重点管理指標の変化がKPIに影響する可能性があります。'),
                'confidence': int(float(top_edge.get('confidence', 0.78)) * 100),
            },
            'lens': ui.get('graph_lens') or [
                {'id': 'l1', 'label': 'Fact graph', 'value': '回答イベントから確認済みの顧客発言と見積状況'},
                {'id': 'l2', 'label': 'Hypothesis graph', 'value': '価格再確認と成約率低下の仮説'},
                {'id': 'l3', 'label': 'Gap graph', 'value': '粗利基準と閾値は未承認'},
                {'id': 'l4', 'label': 'KPI graph', 'value': '見積粗利率・見積成約率との関連'},
            ],
        }

    def kpi_trends(self, company_id: str) -> list[dict[str, Any]] | None:
        data = self.structured(company_id)
        if not data:
            return None
        responses = data.get('survey_responses', [])
        kpi_candidates = {item['kpi_candidate_id']: item for item in data.get('kpi_candidates', [])}

        trends: list[dict[str, Any]] = []
        for metric in data.get('focus_metric_candidates', []):
            signal_types = set(metric.get('observation_signal_types', []))
            history = sorted(
                (
                    {'collected_at': response.get('collected_at'), 'value': response.get('numeric_value')}
                    for response in responses
                    if signal_types & set(response.get('tags', [])) and response.get('numeric_value') is not None
                ),
                key=lambda point: point['collected_at'] or '',
            )
            latest = history[-1] if history else None
            previous = history[-2] if len(history) > 1 else None
            if latest and previous:
                if latest['value'] > previous['value']:
                    direction = 'up'
                elif latest['value'] < previous['value']:
                    direction = 'down'
                else:
                    direction = 'flat'
            else:
                direction = 'new' if latest else 'no_data'

            trends.append({
                'id': metric['focus_metric_candidate_id'],
                'label': metric['metric_name'],
                'category': metric.get('metric_category', ''),
                'description': metric.get('description', ''),
                'latest_value': latest['value'] if latest else None,
                'latest_collected_at': latest['collected_at'] if latest else None,
                'direction': direction,
                'history': history,
                'related_kpis': [
                    kpi_candidates[kpi_id]['kpi_name']
                    for kpi_id in metric.get('related_kpi_candidate_ids', [])
                    if kpi_id in kpi_candidates
                ],
                'trigger_condition': metric.get('trigger_condition', ''),
                'measurement_frequency': metric.get('measurement_frequency', ''),
                'approval_status': metric.get('approval_status', 'proposed'),
            })
        return trends

    def weekly_report(self, company_id: str) -> dict[str, Any] | None:
        data = self.structured(company_id)
        if not data:
            return None
        ui = data.get('ui', {})
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
                'period': ui.get('report_period', f'{company_id} / 2026-07-01 - 2026-07-04'),
                'summary': ui.get('weekly_summary', '重点管理指標の変化を継続観測する必要があります。'),
            },
            'highlights': highlights,
            'snippets': ui.get('report_snippets') or [
                'A社の小ロット案件で価格の再確認が2回発生。',
                '「他社見積と合わせたい」という競合比較の発言あり。',
                'ベテランの見積調整判断が粗利確保に寄与する可能性。',
            ],
            'recommendation': {
                'title': 'Recommended observation',
                'description': ui.get('recommendation', '現場担当へ週次で重点管理指標の変化と背景を確認してください。'),
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
        ui = data.get('ui', {})
        return (
            'サンプルデータに基づく回答です。\n\n'
            f'- 参照企業: {data.get("company", {}).get("company_name", company_id)}\n'
            f'- LLM Wiki: company_profile.md / kpi_definitions.yaml / focus_metrics.yaml / research_policy.yaml を参照対象にしています。\n'
            f'- BigQuery seed: onboarding_answer_events、kpi_candidates、focus_metric_candidates、knowledge_nodes、knowledge_edges 相当の構造化データを参照しています。\n'
            f'- KPI候補: {kpis}\n'
            f'- 重点管理指標候補: {focus_metrics}\n\n'
            f"{ui.get('copilot_conclusion', '現時点では重点管理指標候補を先行指標としてKPI候補を観測するのが妥当です。')}"
            'ただし正式採用と current 定義への反映は人間承認待ちとして扱ってください。'
        )


sample_company_data = SampleCompanyData()
