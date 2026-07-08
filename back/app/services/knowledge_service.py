import json
import re
from app.core.config import settings
from app.crud.bigquery_crud import bigquery_crud
from app.schemas.knowledge import CustomTableProposal, KnowledgeEdge, KnowledgeNode
from app.schemas.survey import SurveyResponseRecord
from app.utils.ids import stable_id
from app.utils.time import utc_now_iso


# 抽出語彙は design §10.1（ノード10型）/ §10.2（エッジ7型）に従う。
# Question / Skill / RELATED_TO は廃止（質問原文は survey_responses が保持し、
# ノード詳細 API の証拠レイヤーから参照する）。
_EXTRACTION_SPECS: list[tuple[str, list[str], float]] = [
    ('TacitKnowledge', ['コツ', '判断', '経験', 'ベテラン', '新人', 'この人', '暗黙', '先回り', '好み',
                        '技術', '接客', '対応', '教育', 'スキル', '高評価'], 0.72),
    ('Signal', ['兆候', 'クレーム', '失注', '離れる', '不満', '問い合わせ', '変化'], 0.70),
    ('Risk', ['リスク', '懸念', '危険', 'トラブル', '退職', '辞め', '故障'], 0.66),
    ('KPI', ['売上', '利益', '件数', '頻度', 'リピート', '単価', '割合'], 0.65),
]

# 同一回答内で共起した抽出/既存ノードの型ペアに応じて張るエッジ（design §10.2）。
# (source型, target型) -> (edge_type, 事実/仮説, strength)
_EDGE_RULES: dict[tuple[str, str], tuple[str, bool, float]] = {
    ('Signal', 'KPI'): ('LEADING_INDICATOR_OF', True, 0.6),
    ('Risk', 'KPI'): ('PRESSURES', False, 0.6),
    ('TacitKnowledge', 'KPI'): ('PROTECTS', False, 0.62),
    ('Person', 'TacitKnowledge'): ('KNOWS', False, 0.62),
}


def _summary_label(text: str, limit: int = 24) -> str:
    """回答文から表示用ラベルを作る（最初の句点まで、長ければ切り詰め）。"""
    head = text.split('。')[0].strip() or text.strip()
    return head[:limit]


class KnowledgeService:
    def extract_from_response(self, company_id: str, response: SurveyResponseRecord) -> tuple[list[KnowledgeNode], list[KnowledgeEdge]]:
        text = response.raw_answer
        nodes: list[KnowledgeNode] = []
        existing = self._match_existing_nodes(company_id, text)
        existing_types = {n['node_type'] for n in existing}
        existing_ids = {n['node_id'] for n in existing}
        for node_type, keywords, confidence in _EXTRACTION_SPECS:
            if not (any(k in text for k in keywords) or (node_type == 'KPI' and response.numeric_value is not None)):
                continue
            # 名寄せ: 同型の既存ノードが回答中で言及されていれば新規ノードは作らず、
            # 既存ノードへのエッジ接続（下の共起ペア処理）に委ねる
            if node_type in existing_types:
                continue
            nodes.append(KnowledgeNode(
                node_id=stable_id('node', company_id, node_type, text[:80], str(response.numeric_value)),
                company_id=company_id,
                node_type=node_type,
                label=_summary_label(text),
                description=text[:500],
                source_response_id=response.response_id,
                confidence=confidence,
                properties={'raw_answer': text, 'numeric_value': response.numeric_value, 'extractor': 'rule_based_mvp'},
            ))
        for person in sorted(set(re.findall(r'[A-ZＡ-Ｚ一-龥ぁ-んァ-ン]{1,12}さん', text))):
            person_id = stable_id('node', company_id, 'Person', person)
            if person_id in existing_ids:
                continue
            nodes.append(KnowledgeNode(
                node_id=person_id,
                company_id=company_id,
                node_type='Person',
                label=person,
                description='回答内で言及された人物',
                source_response_id=response.response_id,
                confidence=0.6,
                properties={'raw_answer': text, 'extractor': 'rule_based_mvp'},
            ))
        edges = self._build_cooccurrence_edges(company_id, response, nodes, existing)
        return nodes, edges

    def _match_existing_nodes(self, company_id: str, text: str) -> list[dict]:
        """既存ノードの label が回答文中に現れるものを返す簡易名寄せ。
        DRY_RUN や BQ 未接続時は query_rows が空を返すので no-op になる。"""
        knowledge_nodes = settings.qualified_table(company_id, 'knowledge_nodes')
        try:
            rows = bigquery_crud.query_rows(f"""
                SELECT node_id, node_type, label FROM `{knowledge_nodes}`
                WHERE status='active' LIMIT 500
            """)
        except Exception:
            return []
        return [
            r for r in rows
            if isinstance(r.get('label'), str) and len(r['label']) >= 2 and r['label'] in text
        ]

    def _build_cooccurrence_edges(
        self,
        company_id: str,
        response: SurveyResponseRecord,
        nodes: list[KnowledgeNode],
        existing: list[dict],
    ) -> list[KnowledgeEdge]:
        """同一回答内の共起ノード（新規抽出＋名寄せ一致の既存ノード）を
        design §10.2 の型ペア規則でエッジ化する。"""
        participants: list[tuple[str, str]] = [(n.node_id, n.node_type) for n in nodes]
        participants += [(r['node_id'], r['node_type']) for r in existing]
        edges: list[KnowledgeEdge] = []
        seen: set[str] = set()
        for source_id, source_type in participants:
            for target_id, target_type in participants:
                if source_id == target_id:
                    continue
                rule = _EDGE_RULES.get((source_type, target_type))
                if rule is None:
                    continue
                edge_type, is_hypothesis, strength = rule
                edge_id = stable_id('edge', company_id, source_id, target_id, edge_type)
                if edge_id in seen:
                    continue
                seen.add(edge_id)
                edges.append(KnowledgeEdge(
                    edge_id=edge_id,
                    company_id=company_id,
                    source_node_id=source_id,
                    target_node_id=target_id,
                    edge_type=edge_type,
                    description='同一回答内の共起から推定された関係' if is_hypothesis else '回答内容から観察された関係',
                    source_response_id=response.response_id,
                    confidence=strength,
                    strength=strength,
                    observed_count=1,
                    properties={'extractor': 'rule_based_mvp', 'hypothesis': is_hypothesis},
                ))
        return edges

    def persist_nodes_edges(self, company_id: str, nodes: list[KnowledgeNode], edges: list[KnowledgeEdge]) -> dict:
        now = utc_now_iso()
        node_rows = [
            {**n.model_dump(), 'properties': json.dumps(n.properties, ensure_ascii=False), 'valid_from': now, 'valid_to': None, 'status': 'active', 'created_at': now, 'updated_at': now}
            for n in nodes
        ]
        edge_rows = [
            {**e.model_dump(), 'properties': json.dumps(e.properties, ensure_ascii=False), 'strength': e.strength if e.strength is not None else e.confidence, 'created_at': now, 'updated_at': now}
            for e in edges
        ]
        return {
            'nodes': bigquery_crud.insert_json_rows(settings.qualified_table(company_id, 'knowledge_nodes'), node_rows) if node_rows else {'inserted': 0},
            'edges': bigquery_crud.insert_json_rows(settings.qualified_table(company_id, 'knowledge_edges'), edge_rows) if edge_rows else {'inserted': 0},
        }

    def propose_custom_table(self, company_id: str, table_id: str, purpose: str, columns: list[dict]) -> CustomTableProposal:
        qualified_table_id = settings.qualified_table(company_id, table_id)
        base_columns = ['record_id STRING NOT NULL', 'company_id STRING NOT NULL']
        custom_columns = [f'{c["name"]} {c.get("type", "STRING")}' for c in columns]
        audit_columns = ['source_response_id STRING', 'properties JSON', 'created_at TIMESTAMP', 'updated_at TIMESTAMP', 'PRIMARY KEY (record_id) NOT ENFORCED']
        ddl = f'CREATE OR REPLACE TABLE `{qualified_table_id}` (\n  ' + ',\n  '.join(base_columns + custom_columns + audit_columns) + '\n);'
        column_lines = '\n'.join([f'- `{c["name"]}`: {c.get("description", c.get("type", "STRING"))}' for c in columns])
        wiki_update = f'''## 任意テーブル追加: `{table_id}`

### 目的
{purpose}

### 管理カラム
{column_lines}

### 運用
Research Agent はこのテーブルに必要な定量・定性情報をアンケートで収集する。
Knowledge Agent は回答から LLM Wiki と BigQuery Graph のノード・エッジを更新する。
'''.strip()
        questions = [
            {'question_text': f'{purpose}について、今週記録すべき出来事・数値・理由はありますか？', 'frequency': 'weekly', 'answer_type': 'text', 'target_role': 'manager'},
            {'question_text': f'{table_id} に追加すべき新しい管理項目や関係者はありますか？', 'frequency': 'monthly', 'answer_type': 'text', 'target_role': 'owner'},
        ]
        return CustomTableProposal(company_id=company_id, table_id=table_id, purpose=purpose, ddl=ddl, wiki_update_markdown=wiki_update, recommended_questions=questions)


knowledge_service = KnowledgeService()
