# サービス事実ベースサマリ

最終更新: 2026-07-09

このドキュメントは、リポジトリ内の実装ファイルと設定ファイルを根拠に、現時点のサービス構成と機能を事実ベースで整理したものです。

## 1. サービスの実体

本リポジトリは、コンサルタント向けに企業ナレッジを継続収集・構造化し、レポート化と人間承認フローを提供するシステムです。

- フロントエンド: Next.js アプリ
- バックエンド: FastAPI API
- エージェント: Google ADK ベースの API サーバ
- データ基盤: BigQuery / Cloud Storage（ローカル時はエミュレーションあり）

根拠:
- `README.md`
- `front/next.config.ts`
- `back/app/main.py`
- `agent/Dockerfile`
- `docker-compose.yaml`

## 2. 実行構成（ローカル）

Docker Compose で以下の主要サービスが起動します。

- `front` (3000)
- `back` (8000)
- `agent` (8080)
- `bigquery-emulator` (9050)
- `ollama` (11434)

フロントは `NEXT_PUBLIC_API_BASE_URL` 経由でバックエンド API を参照します。

根拠:
- `docker-compose.yaml`
- `front/lib/api-client.ts`
- `Makefile`

## 3. 技術スタック（設定ファイル基準）

### Frontend

- Next.js 16.2.9
- React 19.2.7
- TypeScript
- TanStack Query
- Static Export (`output: "export"`)

根拠:
- `front/package.json`
- `front/next.config.ts`

### Backend

- Python 3.12系（開発想定）
- FastAPI
- Pydantic / pydantic-settings
- google-cloud-bigquery / google-cloud-storage
- httpx

根拠:
- `back/pyproject.toml`
- `back/app/main.py`

### Agent

- Python 3.12
- google-adk
- FastAPI/uvicorn 依存あり
- adk `api_server` として起動

根拠:
- `agent/pyproject.toml`
- `agent/Dockerfile`
- `agent/agents/agent.py`

## 4. バックエンド API の実装範囲

`/api/v1` 配下で以下が実装されています。

- health
- companies（作成、論理削除、onboarding prepare）
- survey（初期質問取得、提出）
- dashboard
- knowledge stats / kpi trends
- graph（nodes と query）
- report（weekly / monthly）
- report copilot chat
- approvals（作成、一覧、承認、却下、適用済みマーク）
- research（質問登録、assignment、回答、tick）
- wiki（upload、一覧、versions、content）
- bigquery（core table DDL生成/実行）
- custom table propose
- migrations
- schema validation
- observation signals

根拠:
- `back/app/api/v1/router.py`
- `back/app/api/v1/endpoints/*.py`

## 5. フロントエンド画面（App Router）

確認できる主なページ:

- `/`（Discovery Feed）
- `/intake`
- `/knowledge`
- `/graph`
- `/report`
- `/report-copilot`
- `/report-chat`
- `/research`
- `/approvals`
- `/wiki`
- `/signin`

根拠:
- `front/app/*/page.tsx`
- `front/components/feature/**`

## 6. 中核ユースケース（実装ベース）

### 6.1 月次レポート

`GET /api/v1/companies/{company_id}/report/monthly`

- 先に `tenants/{company_id}/reports/monthly/{YYYY-MM}/report.json` の存在確認
- 存在すれば保存済みJSONを返却
- なければ集計して生成し、保存を試行
- 保存可否やソース状態を `monthly.source` で返却

根拠:
- `back/app/services/dashboard_service.py`
- `back/app/api/v1/endpoints/report.py`

### 6.2 Copilotチャット

`POST /api/v1/companies/{company_id}/report/copilot`

- back が agent API サーバへ転送
- 失敗時はフォールバック回答経路あり
- 特定のツール呼び出し形式を検出した場合、承認キューへ登録する処理あり

根拠:
- `back/app/api/v1/endpoints/copilot.py`
- `back/app/services/copilot_service.py`

### 6.3 追加調査（Research Inbox）

- `research/assignments` 取得
- `research/answers` で回答送信
- 画面上はロール別に未回答質問を処理

根拠:
- `back/app/api/v1/endpoints/research.py`
- `front/components/feature/research/ResearchInbox.tsx`
- `front/services/research-service.ts`

### 6.4 承認フロー（Human-in-the-loop）

- 承認対象を一覧表示
- 承認・却下の操作を API に反映
- UI で payload / diff を確認可能

根拠:
- `back/app/api/v1/endpoints/approvals.py`
- `front/components/feature/approvals/ApprovalsList.tsx`
- `front/services/approval-service.ts`

### 6.5 Wiki閲覧

- current ファイル一覧と version 一覧を取得
- 特定ファイルの content を取得
- フロントで簡易差分表示

根拠:
- `back/app/api/v1/endpoints/wiki.py`
- `front/components/feature/wiki/WikiViewer.tsx`
- `front/services/wiki-service.ts`

## 7. データ保存とローカルフォールバック

- BigQuery クライアントはプロセス内でキャッシュ
- `APP_ENV=local` かつ emulator host 指定時は BigQuery Emulator 利用
- Storage は `dry_run=true` または `WIKI_BUCKET` 未設定時にローカルファイル保存

根拠:
- `back/app/db/bigquery.py`
- `back/app/crud/storage_crud.py`
- `back/app/core/config.py`

## 8. 認証・テナント分離の現状

`TenantAuthMiddleware` は現状パススルーで、認証・認可は未強制です（TODOコメント明記）。

根拠:
- `back/app/middleware/tenant_auth.py`

## 9. テストで確認できる対象

- health エンドポイント
- monthly report 生成/再利用
- onboarding prepare
- survey template 読込
- agent tool の一部挙動
- scoring の clamp

根拠:
- `back/tests/test_health.py`
- `back/tests/test_monthly_report.py`
- `back/tests/test_onboarding.py`
- `back/tests/test_survey_template.py`
- `agent/tests/test_continuous_discovery_tools.py`
- `agent/tests/test_scoring.py`

## 10. 補足

本サマリは「設計意図」よりも「実際に存在するコードと設定」の記述を優先しています。仕様変更時は上記根拠ファイルを優先して更新してください。
