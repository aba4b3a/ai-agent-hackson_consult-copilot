# 実装計画: Continuous Discovery Agent MVP

## 1. 目的

この文書は、要件定義と設計書を実装タスクへ落とし込むための計画です。MVP では、素早い知識形成、根拠検索、コンサルタント向け発見ワークフロー、見える形でのナレッジ蓄積を優先します。

## 2. 実装原則

1. 観測、ナレッジ形成、発見、仮説、追加観測、組織学習のループを保つ。
2. 観測事実と仮説をデータモデル、UI、レポートで分ける。
3. AI 抽出結果は候補として扱い、重要な本番反映には人間承認を挟む。
4. 後から訂正、上書き、廃止できるデータ構造にする。
5. BigQuery を分析用の中核保存先にする。
6. BigQuery Graph を関係性分析に使う。
7. MVP では Spanner / Spanner Graph を使わない。
8. Production deploy、Terraform apply、IAM 変更は自動実行しない。

## 3. タスク一覧

### 3.1 フロントエンド

- `/intake` の初期アンケート回答 UI を維持する。
- `/research` の追加質問 UI を維持する。
- `/knowledge` でナレッジ統計を表示する。
- `/graph` で node / edge を可視化する。
- `/wiki` で current / versions の Wiki を閲覧する。
- `/approvals` で候補承認を扱う。
- `/report` で Monthly Discovery Report と Report Copilot を表示する。
- navigation は `BottomNav.tsx` に集約する。

### 3.2 バックエンド

- 会社単位の API routing を維持する。
- survey response を受け取り、agent runtime へ渡す。
- BigQuery Emulator と本物の BigQuery を環境変数で切り替える。
- Cloud Storage と local storage fallback を切り替える。
- Monthly Discovery Report を保存済み JSON から取得し、ない場合は生成して保存する。
- agent の成功判定では実 side effect を確認する。
- schema validation endpoint と validation 処理を維持する。

### 3.3 エージェント

- `orchestrator_agent` は全体制御と handoff に集中する。
- `research_agent` は追加質問生成に集中する。
- `knowledge_agent` は Wiki、KPI 候補、重点観測項目候補、node / edge 生成を担当する。
- `safe_tool` で tool 例外を構造化する。
- AI 出力 schema を更新した場合は backend / tests も更新する。

### 3.4 インフラ

- Cloud Run multi-container 構成を nginx / back / agent で維持する。
- Artifact Registry への image push 手順を維持する。
- Terraform module 追加時は Cost Guard と IAM 影響を確認する。
- `infra/terraform/environments/dev` に未接続 module を追加する場合は plan 差分をレビューする。

### 3.5 テスト

- backend pytest で onboarding、monthly report、knowledge extraction、graph API、health を確認する。
- agent pytest で scoring と continuous discovery tools を確認する。
- frontend は `npx playwright test` で dashboard / graph などの主要画面を確認する。
- `front/package.json` に `test:e2e` script を追加する場合は Makefile と整合させる。

## 4. 受け入れ条件

- `make dev` で主要サービスが起動する。
- `/report` が保存済みまたは生成済みレポートを表示できる。
- `/graph` が BigQuery の node / edge をもとに表示できる。
- Wiki が current と versions を区別して扱える。
- KPI 候補と本番 KPI 定義が分離されている。
- secret や PII がログ、fixture、ドキュメントに混入していない。
- Cost Guard と Release Gate の前提を破っていない。

## 5. 既知の作業残

- QualityOps 系 agent ファイルは未配線のプレースホルダであり、実装済み agent と誤認しない。
- `make test` が参照する `front` の `test:e2e` script は現状未定義。
- `infra/terraform/environments/dev` は Artifact Registry 以外の module 呼び出しが未接続。
- `.ai-common` 本体は作業ツリーに存在しない場合があるため、プロジェクト固有 overlay の内容を優先して確認する。
