import json
from app.crud.storage_crud import storage_crud


class WikiService:
    def render_initial_wiki(self, company_id: str, company_name: str, initial_survey: dict) -> tuple[str, dict]:
        lines = []
        for q in initial_survey.get('questions', []):
            lines.append(f"- [{q.get('frequency')}] {q.get('question_text')} / 対象: {q.get('target_role')} / 型: {q.get('answer_type')}")
        question_lines = '\n'.join(lines)
        wiki_markdown = f'''# LLM Wiki: {company_name}

## 1. 目的
このWikiは、中小企業内に存在する暗黙知を可視化し、Research Agentによる定期アンケート収集と、Knowledge Agentによる構造化分析の基盤として利用する。

## 2. 企業ID
`{company_id}`

## 3. 暗黙知マップ
初期調査後に、人物、業務、顧客、商品、兆候、KPI、暗黙知を BigQuery Graph のノード・エッジとして追記する。

## 4. 初期アンケート
{question_lines}

## 5. BigQuery基本3テーブル
- `survey_responses`: 定量・定性アンケート回答
- `knowledge_nodes`: 暗黙知、人物、業務、顧客、商品、KPI、兆候などのノード
- `knowledge_edges`: ノード間の関係性

## 6. 運用ルール
- Research Agent はアンケート形式で定量・定性の両方を収集する。
- Knowledge Agent は回答からノードとエッジを抽出する。
- BigQuery Graph は暗黙知・業務・顧客・KPI間の関係性可視化に使う。
- 任意テーブルが追加された場合、Knowledge Agent はこのWikiを更新する。
'''
        wiki_json = {'company_id': company_id, 'company_name': company_name, 'purpose': 'SME tacit knowledge discovery and graph visualization', 'initial_survey': initial_survey, 'core_tables': ['survey_responses', 'knowledge_nodes', 'knowledge_edges']}
        return wiki_markdown, wiki_json

    def upload_company_wiki(self, company_id: str, wiki_markdown: str, wiki_json: dict, schema_sql: str) -> dict:
        base = f'companies/{company_id}'
        return {
            'wiki_md': storage_crud.upload_text(f'{base}/wiki.md', wiki_markdown, 'text/markdown; charset=utf-8'),
            'wiki_json': storage_crud.upload_text(f'{base}/wiki.json', json.dumps(wiki_json, ensure_ascii=False, indent=2), 'application/json; charset=utf-8'),
            'schema_sql': storage_crud.upload_text(f'{base}/schema.sql', schema_sql, 'text/plain; charset=utf-8'),
        }


wiki_service = WikiService()
