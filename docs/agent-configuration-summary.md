# agent/ エージェント構成まとめ

## 位置づけ

`agent/` は Consult Copilot / Continuous Discovery Agent の AI 実行基盤です。Google ADK の `api_server` として起動し、FastAPI backend から `/run` 経由で呼び出されます。

主な実装ファイルは次の通りです。

| 領域 | ファイル | 役割 |
|---|---|---|
| エージェント本体 | `agent/agents/agent.py` | ADK Agent の定義。実運用の中心 |
| プロンプト | `agent/prompts/prompts.py` | Orchestrator / Research / Knowledge の指示 |
| 設定 | `agent/agents/config.py` | `.env` 読み込み、モデル、GCP、dry-run 設定 |
| BigQuery tool | `agent/tools/bigquery_tools.py` | テーブル作成、候補登録、Graph 用 node/edge 更新 |
| Storage tool | `agent/tools/storage_tools.py` | Raw 回答、LLM Wiki、調査スケジュールの GCS 保存 |
| Wiki tool | `agent/tools/wiki_tools.py` | Markdown / YAML / JSON の Wiki 成果物生成 |
| Survey tool | `agent/tools/survey_tools.py` | 初期アンケートテンプレートの参照契約を返す |
| Safety wrapper | `agent/tools/safety.py` | tool 例外を構造化エラーに変換 |
| 出力スキーマ | `agent/agents/schemas.py`, `agent/schemas/*.json` | Research / Knowledge 出力の構造定義 |

## 実際に動くエージェント

`agent/agents/agent.py` には、ADK の `Agent` として次の3体が定義されています。

### 1. orchestrator_agent

`root_agent` として公開される司令塔エージェントです。

主な役割:

- 初期オンボーディング、追加調査、Wiki 更新、BigQuery 反映案の流れを管理する
- `research_agent` と `knowledge_agent` への handoff を制御する
- 初期アンケートの取得、基盤テーブル作成、raw 回答保存など、全体進行に必要な tool を持つ
- KPI や重点管理指標を自分だけで確定しない
- 未承認の KPI / 重点管理指標を current 定義テーブルへ反映しない

登録されている主な tool:

- `ensure_shared_dataset`
- `create_common_tables`
- `create_core_tables`
- `create_tenant_tables`
- `generate_*_ddl`
- `generate_common_initial_survey`
- `write_raw_answer`
- `insert_research_followup_question_events`
- `upsert_current_kpi_definition`
- `upsert_current_focus_metric_definition`
- `propose_custom_table_ddl`
- `sample_graph_query`

重要な設計判断として、`orchestrator_agent` には `write_wiki_files` や `insert_kpi_candidates` が登録されていません。これは、司令塔が分析なしに空の Wiki や空の候補を shortcut 生成することを避けるためです。分析と成果物生成は `knowledge_agent` に寄せています。

### 2. research_agent

現場や事業主への追加質問を作る調査エージェントです。

主な役割:

- `knowledge_agent` が作った `research_plan` に基づいて追加質問を生成する
- 1回の実行で最大3問までに抑える
- 1問1論点、回答者が1分以内に答えられる質問にする
- 役割に応じて聞き方を変える
- KPI や重点管理指標を確定しない
- Wiki や BigQuery の定義テーブルを直接更新しない

登録されている主な tool:

- `generate_common_initial_survey`
- `insert_survey_response`
- `insert_research_followup_question_events`

出力の意図:

- `questions_to_ask`
- `question reasons`
- `target_role`
- `expected_answer_format`
- `needs_followup`
- `answer_summary`
- `handoff_to_knowledge_agent`

### 3. knowledge_agent

回答や観測情報を企業固有のナレッジに変換する中核エージェントです。

主な役割:

- 初期回答、追加回答、観測情報から企業モデルを作る
- KPI 候補、重点管理指標候補、観測方針、追加調査方針を生成する
- LLM Wiki を生成し、GCS に保存する
- BigQuery に候補、質問、Knowledge Graph 用 node / edge を登録する
- 継続収集が必要な指標について、収集用 BigQuery テーブルと GCS 上の schedule 定義を作る
- 根拠が弱い情報を確定値として扱わず、人間承認対象に回す

必須出力:

- `company_profile`
- `kpi_candidates`
- `focus_metric_candidates`
- `observation_policy`
- `research_plan`
- `wiki_files`
- `bigquery_write_plan`
- `human_review_items`

登録されている主な tool:

- BigQuery DDL 生成、テーブル作成
- `insert_onboarding_answer_events`
- `insert_kpi_candidates`
- `insert_focus_metric_candidates`
- `insert_research_followup_question_events`
- `insert_wiki_revision_log`
- `upsert_knowledge_nodes`
- `upsert_knowledge_edges`
- `propose_custom_table_ddl`
- `create_research_collection_table`
- `sample_graph_query`
- Wiki レンダリング系 tool
- `write_wiki_file`
- `write_wiki_files`
- `write_derived_json`
- `upload_company_wiki`
- `register_research_schedule_item`

## 動作フロー

実装上の中心フローは、初期オンボーディングから企業 Wiki 確定までの2段階です。

### Stage 1: 初期アンケート後

`back/app/services/onboarding_service.py` が、初期アンケート回答を受け取ると background task として ADK agent を呼び出します。

処理の流れ:

1. backend が ADK session を作成する
2. `orchestrator_agent` に初期18問の回答を渡す
3. BigQuery の共通 / 企業別テーブルを作成する
4. 初期回答を `onboarding_answer_events` に保存する
5. `knowledge_agent` が KPI 候補、重点管理指標候補、追加質問案を作る
6. `research_agent` または `knowledge_agent` の tool 呼び出しにより、追加質問を `research_followup_question_events` に登録する
7. `knowledge_agent` が draft Wiki を生成して GCS に保存する
8. backend は agent の自然言語応答だけでなく、BigQuery の追加質問件数または GCS の Wiki 更新を見て成功判定する

### Stage 2: 追加質問回答後

追加質問がすべて回答されると、backend が最終化フローを起動します。

処理の流れ:

1. 初期回答と追加質問回答をまとめて agent に渡す
2. `knowledge_agent` が KPI 候補・重点管理指標候補を再評価する
3. 継続観測が必要な項目について、収集テーブルと schedule を作る
4. confirmed Wiki を再生成して GCS に保存する
5. backend は GCS の Wiki 更新を確認して onboarding を `completed` にする

## データの保存先

### BigQuery

BigQuery は構造化ナレッジと分析用データの保存先です。

主なテーブル群:

- `companies`
- `onboarding_question_master`
- `common_kpi_master`
- `{company_id}_onboarding_answer_events`
- `{company_id}_research_followup_question_events`
- `{company_id}_followup_answer_events`
- `{company_id}_kpi_candidates`
- `{company_id}_focus_metric_candidates`
- `{company_id}_current_kpi_definitions`
- `{company_id}_current_focus_metric_definitions`
- `{company_id}_survey_responses`
- `{company_id}_knowledge_nodes`
- `{company_id}_knowledge_edges`

`generate_core_tables_ddl` では BigQuery Graph 用の `PROPERTY GRAPH` も生成します。これにより、企業の顧客、課題、商品、KPI、暗黙知などを node / edge として扱えます。

### Cloud Storage と GCS

GCS は原文証跡、派生 JSON、LLM Wiki、調査スケジュールの保存先です。

主なパス:

- `tenants/{company_id}/raw/fiscal_year={year}/answers/...`
- `tenants/{company_id}/derived/fiscal_year={year}/...`
- `tenants/{company_id}/wiki/current/...`
- `tenants/{company_id}/wiki/versions/{timestamp}/...`
- `tenants/{company_id}/research/schedule.json`

Wiki は current と version snapshot の両方に保存されるため、最新状態と履歴を分けて扱えます。

## 安全設計

### Human-in-the-loop 前提

プロンプト上、次は人間承認が必要とされています。

- 新しい KPI の本番採用、廃止、大幅変更
- 重点管理指標の本番採用、廃止、大幅変更
- BigQuery スキーマ変更
- Wiki の企業理解を大きく変える更新
- confidence が 0.7 未満の情報に基づく更新

また、`upsert_current_kpi_definition` と `upsert_current_focus_metric_definition` は `approved=True` がないと `PermissionError` になります。候補生成と本番定義への昇格が分離されています。

### dry-run 設定

`agent/agents/config.py` の `DRY_RUN` は既定で `true` です。BigQuery や GCS の tool は dry-run 時に実書き込みせず、実行予定の SQL、rows、path、preview を返します。

### safe_tool による保護

すべての主要 tool は `safe_tool` で包まれています。tool 呼び出しの引数不足や型不一致で例外が起きても、agent turn 全体をクラッシュさせず、次のような構造化エラーを返します。

- `error`
- `tool`
- `traceback`

LLM の tool-call は壊れやすいため、このガードは実運用上かなり重要です。

### backend 側の成功判定

backend は agent の「完了しました」という自然言語を信用しすぎない設計です。`onboarding_service.py` では、次の side effect を実際に確認して状態遷移します。

- onboarding follow-up question が BigQuery に作られたか
- Wiki ファイルが GCS に書かれたか

このため、LLM が成功したような文章だけを返した場合でも、実成果物がなければ失敗扱いにできます。

## 未配線のプレースホルダ

`agent/agents/` には次のファイルもありますが、プロジェクト overlay で「未配線のプレースホルダ」と明記されています。

- `cost_guard_agent.py`
- `quality_eval_agent.py`
- `release_gate_agent.py`
- `report_agent.py`
- `test_data_agent.py`
- `ui_review_agent.py`

これらは現状、固定値または簡易 dict を返すだけです。`agent/agents/agent.py` の `root_agent` から import も sub agent 登録もされていません。将来の QualityOps / Release Gate / Report Copilot 用の実装先候補ですが、現在の Continuous Discovery Agent 本体とは区別する必要があります。

## モデルと起動方式

### モデル設定

`MODEL_ID` で ADK Agent のモデルを切り替えます。

既定値:

```text
ollama_chat/gemma4:12b
```

Gemini / Vertex AI を使う場合は `agent/GEMINI_SETUP.md` に設定メモがあります。重要なのは、実装が読む主要変数は `MODEL_ID`, `PROJECT_ID` / `GCP_PROJECT`, `LOCATION`, `DRY_RUN`, `APP_ENV` である点です。

### 起動

`agent/Dockerfile` は次のコマンドで ADK api_server を起動します。

```bash
adk api_server --host 0.0.0.0 --port 8080 agents
```

Cloud Run の multi-container 構成では、nginx が public ingress となり、`/agent` を agent sidecar に proxy する想定です。ローカルでは backend が `AGENT_BASE_URL` 経由で agent API にアクセスします。

## アピールポイント

### 1. 役割分担が明確な multi-agent 構成

司令塔、調査、ナレッジ形成を分けています。特に `orchestrator_agent` に強い分析 tool を持たせすぎず、実際の抽出・Wiki 生成を `knowledge_agent` に寄せている点は良い設計です。責務が混ざると、LLM が「それっぽい空成果物」を作ってしまうため、tool の登録範囲で事故を防いでいます。

### 2. 候補生成と本番反映が分離されている

KPI / 重点管理指標はまず candidate として登録され、current 定義への昇格には承認が必要です。コンサルティング用途では、AI が経営判断を代行しないことが重要なので、この分離はプロダクトの信頼性に直結します。

### 3. LLM Wiki と BigQuery Graph の両立

人間が読める Wiki と、機械が分析できる BigQuery / BigQuery Graph の両方を生成する構成です。これにより、コンサルタント向けの説明可能性と、Graph UI / 分析基盤への展開を同時に満たせます。

### 4. agent の自己申告に頼らない検証

backend が GCS や BigQuery の実 side effect を確認して onboarding の成功を判定します。LLM アプリでは「モデルが成功と言ったが実際は保存されていない」問題が起きやすいため、これは実装上の大きな強みです。

### 5. dry-run と emulator 前提で開発しやすい

`DRY_RUN=true` が既定で、BigQuery emulator や Ollama ローカル LLM も想定されています。クラウド費用や本番データへの影響を抑えながら、agent の tool chain を検証できます。

### 6. 継続調査まで設計に含まれている

単発のアンケート分析で終わらず、`create_research_collection_table` と `register_research_schedule_item` により、今後も集めるべき情報を schedule 化できます。Continuous Discovery Agent という名前通り、企業理解を継続更新する仕組みがあります。

## 注意点・改善余地

- `agent/agents/agent.py` の `description` 文字列は、端末表示上 mojibake して見えます。実行には大きく影響しない可能性がありますが、運用・保守性のため UTF-8 として正常表示されるか確認した方がよいです。
- `quality_eval_agent.py` などの QualityOps 系ファイルはまだ本体ではありません。資料化やデモ時に「実装済み agent」と誤解しないよう注意が必要です。
- schema validator と JSON schema はありますが、現在の `root_agent` の tool chain 全体で常に自動適用されているわけではありません。重要な downstream decision では、backend または agent flow 上で schema validation を明示的に通す設計に寄せるとより堅くなります。
- 多数の tool を一度に使う multi-step agent なので、モデルの malformed function call や timeout への対策が必要です。backend には retry と side effect 検証が入っていますが、プロンプト・tool schema・タスク分割の継続改善余地があります。

## まとめ

`agent/` の本体は、`orchestrator_agent`、`research_agent`、`knowledge_agent` の3体による Google ADK multi-agent 構成です。

この構成は、初期回答を受け取り、追加質問を作り、企業固有の KPI 候補・重点管理指標候補・Knowledge Graph・LLM Wiki・継続調査スケジュールへ変換することを目的にしています。

良い点は、単なるチャット agent ではなく、BigQuery / GCS / Wiki / Graph / human approval を含む業務フローとして設計されていることです。特に、AI の推論を候補として扱い、人間承認を経て本番定義に昇格する流れは、コンサルティング支援プロダクトとして説得力があります。
