# ai-agent-hackson_consult-copilot

## Current Development Flow

Use Dev Containers or VS Code Server / Remote SSH with the host Docker Engine,
then run services with Docker Compose from this `repo-base/` directory. Docker
in Docker is not required for local development.

```bash
make setup
make dev
```

The Makefile runs setup, lint, tests, and builds through Docker Compose, so the
host only needs Docker and Compose for the normal workflow. When using Dev
Containers, the container uses the host Docker socket through
`docker-outside-of-docker`.

各種システム開発のベースとして利用するための初期開発資材です。

`doc\architecture\base-architecture\ai_qualityops_architecture_design.md` の構成をもとにしていますが、このディレクトリ自体は特定の 1 システムに閉じた実装ではなく、フロントエンド、バックエンド、AI エージェント、インフラ、CI、ローカル開発環境をまとめた再利用可能な土台として扱います。

## 構成

```text
front/   Next.js 16 + React 19.2 + TypeScript
back/    Python 3.12 + FastAPI
agent/   Python 3.12 の AI エージェント用スケルトン
infra/   Terraform / Cloud Build / Firebase Hosting / Cloud Run
docs/    設計、ローカル開発、コスト、セキュリティ、デモ手順
```

## 技術スタック

### Frontend

- Node.js 24 LTS
- Next.js 16.0.0
- React 19.2.0
- TypeScript
- Static Export
- Firebase Hosting 想定

### Backend

- Python 3.12
- FastAPI
- uv
- ruff / mypy / pytest
- Cloud Run 想定
- ローカル検証用 BigQuery Emulator

### Agent

- Python 3.12
- Pydantic による構造化出力
- prompt / tool / eval の初期配置
- Gemini / ADK 連携は保留

### Infra

- Terraform
- Cloud Build
- Cloud Run
- Firebase Hosting
- Secret Manager
- Artifact Registry

## セットアップ

Dev Containers または VS Code Server / Remote SSH とホスト側 Docker Engine を使います。Docker in Docker は不要です。

ホスト側に以下を用意します。

- Docker Desktop
- Visual Studio Code
- VS Code 拡張機能: Dev Containers

Windows でパッケージマネージャーを使う場合は、Chocolatey だけでなく winget でも構いません。

```powershell
winget install Docker.DockerDesktop
winget install Microsoft.VisualStudioCode
```

Chocolatey を使う場合の例:

```powershell
choco install docker-desktop vscode -y
```

セットアップ手順:

1. Docker Desktop を起動します。
2. VS Code でこのリポジトリの `repo-base/` ディレクトリを開きます。
3. Dev Container を使う場合は `Dev Containers: Reopen in Container` を実行します。
4. `repo-base/` でセットアップを実行します。

```bash
make setup
```

## ローカル起動

ホスト側に Node.js、Python、uv、BigQuery Emulator を個別に入れる必要はありません。Docker Compose が各サービスを起動します。Dev Container 内から実行する場合も、Docker daemon はホスト側のものを使います。

```bash
make dev
```

起動後の確認先:

- Frontend: http://localhost:3000
- Report: http://localhost:3000/report
- Backend API: http://localhost:8000
- Backend health: http://localhost:8000/healthz
- Backend OpenAPI定義： http://localhost:8000/docs
- BigQuery Emulator: http://localhost:9050

## Report 画面

`/report` は前月分の Monthly Discovery Report を表示します。バックエンドは
`GET /api/v1/companies/{company_id}/report/monthly` で
`tenants/{company_id}/reports/monthly/{YYYY-MM}/report.json` を Cloud Storage
またはローカル storage emulator から探索します。

対象月のレポート JSON が存在する場合は保存済みレポートを表示し、存在しない場合は
BigQuery の `knowledge_nodes` / `survey_responses`、または DRY_RUN 用の seed data
から月次レポートを生成して同じパスに保存します。画面にはサマリ、KPI/根拠件数の
グラフ、事実と仮説を分けたハイライト、根拠スニペット、Copilot 質問欄を表示します。

## よく使うコマンド

```bash
make setup
make dev
make lint
make test
make build
make clean
```

## 個別検証

Makefile 経由で Docker Compose サービス内のツールを実行します。

```bash
make lint
make test
make build
```

## 実装方針

- `front/` は Static Export 前提で実装します。
- MVP では SSR、Server Actions、API Routes は使いません。
- API 呼び出しは `NEXT_PUBLIC_API_BASE_URL` 経由で `back/` に寄せます。
- `package-lock.json` と `uv.lock` はコミット対象です。
- AI の判定は提案に留め、最終承認は人間が行います。
- `.env`、サービスアカウントキー、その他シークレットはコミットしません。

## 現在の状態

- Dashboard UI skeleton: 配置済み
- FastAPI health endpoint: 配置済み
- Monthly Report API and report viewer: 配置済み
- Quality run placeholder API: 配置済み
- Agent evaluation skeleton: 配置済み
- Cloud Build / Terraform skeleton: 配置済み
- Gemini / ADK integration: 保留
