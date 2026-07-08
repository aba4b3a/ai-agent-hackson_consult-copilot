import re
from app.core.config import settings
from app.crud.bigquery_crud import bigquery_crud
from app.schemas.knowledge import CustomTableProposal, KnowledgeEdge, KnowledgeNode
from app.schemas.survey import SurveyResponseRecord
from app.utils.ids import stable_id
from app.utils.time import utc_now_iso


class KnowledgeService:
    def extract_from_response(self, company_id: str, response: SurveyResponseRecord) -> tuple[list[KnowledgeNode], list[KnowledgeEdge]]:
        text = response.raw_answer
        nodes: list[KnowledgeNode] = []
        edges: list[KnowledgeEdge] = []
        question_node = KnowledgeNode(
            node_id=stable_id('node', company_id, 'Question', response.question_id),
            company_id=company_id,
            node_type='Question',
            label=response.question_text[:80],
            description='アンケート質問',
            source_response_id=response.response_id,
            confidence=1.0,
            properties={'answer_type': response.answer_type, 'frequency': response.survey_frequency},
        )
        nodes.append(question_node)
        specs = [
            ('TacitKnowledge', '暗黙知候補', ['コツ', '判断', '経験', 'ベテラン', '新人', 'この人', '暗黙', '先回り', '好み'], 0.72),
            ('Signal', '顧客・現場の兆候', ['兆候', 'クレーム', '失注', '離れる', '不満', '問い合わせ', '変化'], 0.70),
            ('Skill', '属人スキル候補', ['技術', '接客', '対応', '教育', 'スキル', '高評価'], 0.68),
            ('KPI', '定量管理候補', ['売上', '利益', '件数', '頻度', 'リピート', '単価', '割合'], 0.65),
        ]
        for node_type, label, keywords, confidence in specs:
            if any(k in text for k in keywords) or (node_type == 'KPI' and response.numeric_value is not None):
                nodes.append(KnowledgeNode(
                    node_id=stable_id('node', company_id, node_type, text[:80], str(response.numeric_value)),
                    company_id=company_id,
                    node_type=node_type,
                    label=label,
                    description=text[:500],
                    source_response_id=response.response_id,
                    confidence=confidence,
                    properties={'raw_answer': text, 'numeric_value': response.numeric_value, 'extractor': 'rule_based_mvp'},
                ))
        for person in sorted(set(re.findall(r'[A-ZＡ-Ｚ一-龥ぁ-んァ-ン]{1,12}さん', text))):
            nodes.append(KnowledgeNode(
                node_id=stable_id('node', company_id, 'Person', person),
                company_id=company_id,
                node_type='Person',
                label=person,
                description='回答内で言及された人物',
                source_response_id=response.response_id,
                confidence=0.6,
                properties={'raw_answer': text},
            ))
        for node in nodes[1:]:
            edges.append(KnowledgeEdge(
                edge_id=stable_id('edge', company_id, question_node.node_id, node.node_id, 'RELATED_TO'),
                company_id=company_id,
                source_node_id=question_node.node_id,
                target_node_id=node.node_id,
                edge_type='RELATED_TO',
                description='質問回答から抽出された関係',
                source_response_id=response.response_id,
                confidence=min(0.9, node.confidence),
                strength=node.confidence,
                observed_count=1,
                properties={'extractor': 'rule_based_mvp'},
            ))
        people = [n for n in nodes if n.node_type == 'Person']
        knowledge_like = [n for n in nodes if n.node_type in {'TacitKnowledge', 'Skill'}]
        for person in people:
            for target in knowledge_like:
                edges.append(KnowledgeEdge(
                    edge_id=stable_id('edge', company_id, person.node_id, target.node_id, 'KNOWS'),
                    company_id=company_id,
                    source_node_id=person.node_id,
                    target_node_id=target.node_id,
                    edge_type='KNOWS',
                    description='人物が持つ可能性のある暗黙知・スキル',
                    source_response_id=response.response_id,
                    confidence=0.62,
                    strength=0.62,
                    observed_count=1,
                    properties={'extractor': 'rule_based_mvp'},
                ))
        return nodes, edges

    def persist_nodes_edges(self, company_id: str, nodes: list[KnowledgeNode], edges: list[KnowledgeEdge]) -> dict:
        now = utc_now_iso()
        node_rows = [{**n.model_dump(), 'valid_from': now, 'valid_to': None, 'status': 'active', 'created_at': now, 'updated_at': now} for n in nodes]
        edge_rows = [{**e.model_dump(), 'strength': e.strength if e.strength is not None else e.confidence, 'created_at': now, 'updated_at': now} for e in edges]
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
