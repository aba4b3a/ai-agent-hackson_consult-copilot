# Continuous Discovery Agent

中小企業の暗黙知をアンケート形式で収集し、BigQuery Graph と Cloud Storage Wiki に構造化するマルチエージェントMVPです。

## Agents

- `command_agent`: 司令塔
- `research_agent`: 質問・調査・定期アンケート
- `knowledge_agent`: 分析・構造化・Wiki作成・BigQuery Graph設計

## Basic Tables

企業ごとに dataset を作成し、以下の3テーブルを作ります。

- `survey_responses`
- `knowledge_nodes`
- `knowledge_edges`

その上に BigQuery Property Graph を作成します。

## Setup

```bash
cp .env.example .env
pip install -e .
```

## Run with ADK

```bash
adk web
```

ADK Web UIで `cda_agents` を選択し、以下のように依頼します。

```text
company_id=company_001 の初期オンボーディングを開始してください。
基本3テーブルのDDLを生成し、初期アンケートを作成してください。
```

## Local dry run

`.env` で `DRY_RUN=true` にすると、BigQuery / Cloud Storage へは書き込まず、SQLやWiki案のみ返します。

## Production

`.env` で以下を設定してください。

```bash
PROJECT_ID="your-project"
WIKI_BUCKET="your-bucket"
DRY_RUN="false"
MODEL_ID="gemini-3.1-pro"
```

## Example prompts

### 初期構築

```text
company_id=company_001, company_name=田中美容室 として、
中小企業の暗黙知可視化用の初期アンケート、BigQuery基本3テーブル、BigQuery Graph定義、LLM Wiki初版を作成してください。
```

### 任意テーブル追加

```text
company_001 に staff_training_records という任意テーブルを追加したい。
スタッフ名、技術項目、現在レベル、目標レベル、指導者コメント、次回アクションを管理したい。
Knowledge AgentでDDLとWiki更新案を作ってください。
```

### Graph可視化用クエリ

```text
company_001 の暗黙知グラフから、顧客離脱に関係するノードとエッジを可視化するGQLを作ってください。
```

## Notes

- BigQuery Graph は Preview/更新中の機能であるため、Google Cloud の最新ドキュメントに合わせて DDL を調整してください。
- テーブル作成や任意テーブル追加は、人間承認を挟む前提です。
