from __future__ import annotations

import json


def render_wiki_markdown(company_id: str, company_name: str, nodes: list[dict], edges: list[dict], recommended_questions: list[dict], custom_tables: list[dict] | None = None) -> str:
    custom_tables = custom_tables or []
    node_lines = "\n".join(f"- `{n.get('node_id')}` [{n.get('node_type')}]: {n.get('label')} - {n.get('description', '')}" for n in nodes) or "- まだ抽出されたノードはありません。"
    edge_lines = "\n".join(f"- `{e.get('source_node_id')}` -[{e.get('edge_type')}]-> `{e.get('target_node_id')}`: {e.get('description', '')}" for e in edges) or "- まだ抽出された関係性はありません。"
    question_lines = "\n".join(f"- [{q.get('frequency')}] {q.get('question_text')} / 対象: {q.get('target_role')} / 型: {q.get('answer_type')}" for q in recommended_questions) or "- まだ推奨質問はありません。"
    table_lines = "\n".join(f"- `{t.get('table_id')}`: {t.get('purpose')}" for t in custom_tables) or "- 任意テーブルはまだありません。"
    return f"""# LLM Wiki: {company_name}

## 1. 目的

このWikiは、中小企業内に存在する暗黙知を可視化し、Research Agentによる定期アンケート収集と、Knowledge Agentによる構造化分析の基盤として利用する。

## 2. 企業ID

`{company_id}`

## 3. 暗黙知ノード

{node_lines}

## 4. 関係性エッジ

{edge_lines}

## 5. 推奨アンケート項目

{question_lines}

## 6. BigQuery Graph

基本3テーブル:

- `survey_responses`: 定量・定性アンケート回答
- `knowledge_nodes`: 暗黙知、人物、業務、顧客、商品、KPI、兆候などのノード
- `knowledge_edges`: ノード間の関係性

## 7. 任意テーブル

{table_lines}

## 8. 運用ルール

- Research Agent はアンケート形式で定量・定性の両方を収集する。
- Knowledge Agent は回答からノードとエッジを抽出する。
- BigQuery Graph は暗黙知・業務・顧客・KPI間の関係性可視化に使う。
- 任意テーブルが追加された場合、Knowledge Agent はこのWikiを更新する。
"""


def render_wiki_json(company_id: str, company_name: str, nodes: list[dict], edges: list[dict], recommended_questions: list[dict], custom_tables: list[dict] | None = None) -> dict:
    return {
        "company_id": company_id,
        "company_name": company_name,
        "purpose": "SME tacit knowledge discovery and graph-based visualization",
        "nodes": nodes,
        "edges": edges,
        "recommended_questions": recommended_questions,
        "custom_tables": custom_tables or [],
    }


def build_custom_table_wiki_update(table_proposal: dict) -> str:
    return f"""
## 任意テーブル追加: `{table_proposal['table_id']}`

### 目的

{table_proposal['purpose']}

### BigQuery DDL

```sql
{table_proposal['ddl']}
```

### 運用

このテーブルは、基本3テーブルでは表現しきれない企業固有の管理対象を扱う。
Research Agent はこのテーブルに必要な情報をアンケートで収集し、
Knowledge Agent は回答内容からWikiとGraphノード・エッジを更新する。
""".strip()


def to_pretty_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)
