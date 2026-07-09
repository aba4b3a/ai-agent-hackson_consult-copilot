"""Graph API（design §10.4〜10.6）のサービス層。

BigQuery の knowledge_nodes / knowledge_edges を読み、DRY_RUN=true や
未投入時は storage_seed の structured_knowledge.json にフォールバックする。
スライス・検索はメモリ上で行う（MVP のノード数は数百件規模のため、
エミュレータ互換性を優先して SQL/GQL では絞り込まない）。
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import settings
from app.services.dashboard_service import _query
from app.services.sample_company_data import sample_company_data

PERIOD_DAYS = {'last_7_days': 7, 'last_30_days': 30, 'last_90_days': 90}

# 読み込み上限。design §10.4 の limit(≤100) より十分大きく取る。
_NODE_FETCH_LIMIT = 500
_EDGE_FETCH_LIMIT = 1000


def _parse_ts(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            return None
    return None


def _within_period(value: Any, cutoff: datetime | None) -> bool:
    """created_at が cutoff 以降なら True。値が無い/読めない行は除外しない
    （seed データは created_at を持たないため）。"""
    if cutoff is None:
        return True
    ts = _parse_ts(value)
    return ts is None or ts >= cutoff


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _parse_properties(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value:
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else None
        except ValueError:
            return None
    return None


def _isoformat(value: Any) -> str | None:
    ts = _parse_ts(value)
    if ts:
        return ts.isoformat()
    return value if isinstance(value, str) and value else None


class GraphService:
    # ── データ読み込み ────────────────────────────────────────────────
    def _load_graph(self, company_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], bool]:
        """(nodes, edges, is_sample) を返す。BQ が空なら seed にフォールバック。"""
        knowledge_nodes = settings.qualified_table(company_id, 'knowledge_nodes')
        knowledge_edges = settings.qualified_table(company_id, 'knowledge_edges')
        node_rows = _query(f"""
            SELECT node_id, node_type, label, description, confidence, status,
                   source_response_id, properties, created_at, updated_at
            FROM `{knowledge_nodes}`
            WHERE status='active' LIMIT {_NODE_FETCH_LIMIT}
        """)
        if node_rows:
            edge_rows = _query(f"""
                SELECT edge_id, source_node_id, target_node_id, edge_type, description,
                       strength, observed_count, source_response_id, created_at
                FROM `{knowledge_edges}` LIMIT {_EDGE_FETCH_LIMIT}
            """)
            return node_rows, edge_rows, False
        data = sample_company_data.structured(company_id) or {}
        nodes = [n for n in data.get('knowledge_nodes', []) if n.get('status', 'active') == 'active']
        return nodes, data.get('knowledge_edges', []), True

    def _load_responses(self, company_id: str, response_ids: set[str], is_sample: bool) -> list[dict[str, Any]]:
        if not response_ids:
            return []
        if is_sample:
            data = sample_company_data.structured(company_id) or {}
            rows = [r for r in data.get('survey_responses', []) if r.get('response_id') in response_ids]
        else:
            survey_responses = settings.qualified_table(company_id, 'survey_responses')
            id_list = ', '.join("'" + rid.replace("'", "\\'") + "'" for rid in sorted(response_ids))
            rows = _query(f"""
                SELECT response_id, question_text, raw_answer, respondent_role, collected_at
                FROM `{survey_responses}`
                WHERE response_id IN ({id_list})
            """)
        return sorted(rows, key=lambda r: str(r.get('collected_at') or ''))

    # ── §10.4 Graph Slice ────────────────────────────────────────────
    def get_slice(
        self,
        company_id: str,
        center_node_id: str | None,
        depth: int,
        limit: int,
        types: str | None,
        period: str,
    ) -> dict[str, Any] | None:
        """center_node_id が見つからない場合は None（呼び出し側で 404）。"""
        nodes, edges, is_sample = self._load_graph(company_id)

        cutoff: datetime | None = None
        if period in PERIOD_DAYS:
            cutoff = datetime.now(timezone.utc) - timedelta(days=PERIOD_DAYS[period])
        nodes = [n for n in nodes if _within_period(n.get('created_at'), cutoff)]
        node_map = {n['node_id']: n for n in nodes}
        edges = [
            e for e in edges
            if _within_period(e.get('created_at'), cutoff)
            and e.get('source_node_id') in node_map
            and e.get('target_node_id') in node_map
        ]
        type_set = {t.strip() for t in types.split(',') if t.strip()} if types else None

        if center_node_id is not None:
            if center_node_id not in node_map:
                return None
            selected_ids, truncated = self._slice_around_center(
                center_node_id, depth, limit, type_set, node_map, edges)
        else:
            candidates = [
                n for n in nodes
                if type_set is None or n.get('node_type') in type_set
            ]
            candidates.sort(key=lambda n: -_to_float(n.get('confidence')))
            truncated = len(candidates) > limit
            selected_ids = {n['node_id'] for n in candidates[:limit]}

        out_edges = sorted(
            (e for e in edges
             if e.get('source_node_id') in selected_ids and e.get('target_node_id') in selected_ids),
            key=lambda e: -_to_float(e.get('strength')),
        )
        out_nodes = sorted(
            (node_map[node_id] for node_id in selected_ids),
            key=lambda n: -_to_float(n.get('confidence')),
        )
        return {
            'nodes': [
                {
                    'node_id': n['node_id'],
                    'node_type': n.get('node_type', 'Unknown'),
                    'label': n.get('label'),
                    'description': n.get('description'),
                    'confidence': n.get('confidence'),
                    'status': n.get('status'),
                }
                for n in out_nodes
            ],
            'edges': [
                {
                    'source_node_id': e['source_node_id'],
                    'target_node_id': e['target_node_id'],
                    'edge_type': e.get('edge_type', 'OBSERVES'),
                    'strength': e.get('strength'),
                    'observed_count': e.get('observed_count'),
                    'description': e.get('description'),
                }
                for e in out_edges
            ],
            'meta': {
                'truncated': truncated,
                'center_node_id': center_node_id,
                'period': period,
                'source': 'sample' if is_sample else 'bigquery',
            },
        }

    def _slice_around_center(
        self,
        center_node_id: str,
        depth: int,
        limit: int,
        type_set: set[str] | None,
        node_map: dict[str, dict[str, Any]],
        edges: list[dict[str, Any]],
    ) -> tuple[set[str], bool]:
        """中心ノードから無向 BFS（§10.4: depth は edge_type 不問・無向）。
        超過時は strength 降順 → confidence 降順で切り詰める。"""
        adjacency: dict[str, list[tuple[str, float]]] = {}
        for e in edges:
            src, dst = e['source_node_id'], e['target_node_id']
            strength = _to_float(e.get('strength'))
            adjacency.setdefault(src, []).append((dst, strength))
            adjacency.setdefault(dst, []).append((src, strength))

        reached: dict[str, float] = {center_node_id: 1.0}  # node_id -> 最大到達 strength
        frontier = [center_node_id]
        for _ in range(depth):
            next_frontier: list[str] = []
            for node_id in frontier:
                for neighbor, strength in adjacency.get(node_id, []):
                    if neighbor not in reached:
                        reached[neighbor] = strength
                        next_frontier.append(neighbor)
                    else:
                        reached[neighbor] = max(reached[neighbor], strength)
            frontier = next_frontier

        # 型フィルタ（中心ノードは対象外 = 常に残す）
        candidates = [
            node_id for node_id in reached
            if node_id == center_node_id
            or type_set is None
            or node_map[node_id].get('node_type') in type_set
        ]
        truncated = len(candidates) > limit
        others = sorted(
            (node_id for node_id in candidates if node_id != center_node_id),
            key=lambda node_id: (
                -reached[node_id],
                -_to_float(node_map[node_id].get('confidence')),
            ),
        )
        return {center_node_id, *others[: max(0, limit - 1)]}, truncated

    # ── §10.5 Entity Search ──────────────────────────────────────────
    def search_entities(self, company_id: str, q: str, types: str | None, limit: int) -> list[dict[str, Any]]:
        nodes, _, _ = self._load_graph(company_id)
        type_set = {t.strip() for t in types.split(',') if t.strip()} if types else None
        needle = q.lower()
        hits = [
            n for n in nodes
            if (type_set is None or n.get('node_type') in type_set)
            and (needle in str(n.get('label') or '').lower()
                 or needle in str(n.get('description') or '').lower())
        ]
        hits.sort(key=lambda n: -_to_float(n.get('confidence')))
        return [
            {
                'node_id': n['node_id'],
                'node_type': n.get('node_type', 'Unknown'),
                'label': n.get('label'),
                'confidence': n.get('confidence'),
            }
            for n in hits[:limit]
        ]

    # ── §10.6 Node Detail / Evidence ─────────────────────────────────
    def get_node_detail(self, company_id: str, node_id: str) -> dict[str, Any] | None:
        """見つからない場合は None（呼び出し側で 404）。"""
        nodes, edges, is_sample = self._load_graph(company_id)
        node_map = {n['node_id']: n for n in nodes}
        node = node_map.get(node_id)
        if node is None:
            return None

        adjacent: list[dict[str, Any]] = []
        for e in edges:
            src, dst = e.get('source_node_id'), e.get('target_node_id')
            if node_id == src:
                direction, other_id = 'outgoing', dst
            elif node_id == dst:
                direction, other_id = 'incoming', src
            else:
                continue
            adjacent.append({
                'edge_id': e.get('edge_id'),
                'direction': direction,
                'edge_type': e.get('edge_type', 'OBSERVES'),
                'description': e.get('description'),
                'strength': e.get('strength'),
                'observed_count': e.get('observed_count'),
                'other_node_id': other_id,
                'other_node_label': (node_map.get(other_id) or {}).get('label'),
                'source_response_id': e.get('source_response_id'),
            })
        adjacent.sort(key=lambda a: -_to_float(a.get('strength')))

        # 証拠レイヤー（§10.0/§10.6）: ノード自身と隣接エッジの source_response_id を
        # survey_responses の原文に解決する
        response_ids = {
            rid for rid in (
                node.get('source_response_id'),
                *(a.get('source_response_id') for a in adjacent),
            )
            if isinstance(rid, str) and rid
        }
        evidence = [
            {
                'response_id': r['response_id'],
                'question_text': r.get('question_text'),
                'raw_answer': r.get('raw_answer'),
                'respondent_role': r.get('respondent_role'),
                'collected_at': _isoformat(r.get('collected_at')),
            }
            for r in self._load_responses(company_id, response_ids, is_sample)
        ]

        return {
            'node_id': node['node_id'],
            'node_type': node.get('node_type', 'Unknown'),
            'label': node.get('label'),
            'description': node.get('description'),
            'confidence': node.get('confidence'),
            'status': node.get('status'),
            'source_response_id': node.get('source_response_id'),
            'properties': _parse_properties(node.get('properties')),
            'created_at': _isoformat(node.get('created_at')),
            'updated_at': _isoformat(node.get('updated_at')),
            'adjacent_edges': adjacent,
            'evidence': evidence,
            'source': 'sample' if is_sample else 'bigquery',
        }


graph_service = GraphService()
