# ローカル開発

このドキュメントは、Consult Copilot / Continuous Discovery Agent をローカルで起動・検証するための手順です。原則としてホストには Docker と VS Code だけを置き、言語ランタイムやエミュレータは Docker Compose 内で動かします。

## 構成

```text
front/   Next.js 開発サーバー
back/    FastAPI
agent/   Google ADK api_server
infra/   nginx / Cloud Run sidecar 再現用設定
docs/    補足資料
```

通常開発では `dev` profile、本番 Cloud Run の sidecar 構成を再現したい場合は `sidecar` profile を使います。

## 前提

- Docker Desktop
- Visual Studio Code
- Dev Containers 拡張機能
- Git

Dev Container を使う場合でも Docker daemon はホスト側のものを使います。

## 初回セットアップ

```bash
make setup
```

このコマンドは依存関係の同期、ローカル検証に必要な初期化、各パッケージの準備を行います。

## 開発サーバー起動

```bash
make dev
```

主な確認先:

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Backend health: http://localhost:8000/healthz
- Backend OpenAPI: http://localhost:8000/docs
- Monthly Report: http://localhost:3000/report
- BigQuery Emulator: http://localhost:9050
- Ollama: http://localhost:11434

## Cloud Run sidecar 再現

Cloud Run の multi-container 構成に近い状態をローカルで検証する場合は、次を使います。

```bash
make sidecar
```

確認例:

```bash
curl http://localhost:8080/
curl http://localhost:8080/api/v1/health
curl http://localhost:8080/agent/list-apps
```

`nginx` が public ingress になり、`/api` を backend、`/agent` を ADK agent runtime へ proxy します。

## Ollama モデル準備

ローカル LLM を使う場合は、起動後に必要なモデルを pull します。

```bash
docker compose exec ollama ollama pull gemma4:12b
```

Gemini / Vertex AI を使う場合は `agent/GEMINI_SETUP.md` を参照してください。

## よく使うコマンド

```bash
make setup
make dev
make sidecar
make lint
make test  # front の test:e2e script は未定義。必要に応じて個別実行
make build
make clean
```

ログ確認:

```bash
docker compose logs -f
docker compose logs -f back
docker compose logs -f agent
docker compose logs -f front
```

サービス再起動:

```bash
docker compose restart back
docker compose restart agent
docker compose restart front
```

コンテナ内でのコマンド実行:

```bash
docker compose exec back pytest
docker compose exec back ruff check app
docker compose exec front npm run lint
docker compose exec front npm run typecheck
docker compose exec agent pytest
```

## 環境変数

ローカルでは `.env.local` または Docker Compose の environment を使います。シークレットはコミットしません。

主な値:

```text
APP_ENV=local
DRY_RUN=true
PROJECT_ID=local-project
BQ_DATASET_PREFIX=consultant_copilot
BIGQUERY_EMULATOR_HOST=http://bigquery-emulator:9050
AGENT_BASE_URL=http://agent:8080
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

本番相当では BigQuery Emulator を無効化し、Secret Manager と Workload Identity Federation を前提にします。

## 現状の注意点

- `Makefile` の `test` target は `front npm run test:e2e` を呼びますが、現状 `front/package.json` に `test:e2e` script はありません。Playwright を実行する場合は `front/` で `npx playwright test` を使います。
- `Makefile` の `lint` target は `front npm run typecheck` を呼びます。こちらは `front/package.json` に定義済みです。

## トラブルシュート

### ポートが使用中

```bash
netstat -ano | findstr :3000
netstat -ano | findstr :8000
```

該当プロセスを停止するか、Docker Compose 側のポートを変更します。

### BigQuery Emulator に接続できない

```bash
docker compose ps bigquery-emulator
docker compose logs -f bigquery-emulator
docker compose restart bigquery-emulator
```

### Ollama に接続できない

```bash
docker compose ps ollama
docker compose logs -f ollama
docker compose exec ollama ollama list
```

### メモリ不足

Ollama や大きめのモデルを使う場合は、Docker Desktop の割り当てメモリを増やします。必要に応じて `docker-compose.yaml` の resource limit も調整します。

## API の主な確認先

- `GET /healthz`
- `GET /api/v1/companies`
- `GET /api/v1/companies/{company_id}/report/monthly`
- `GET /api/v1/companies/{company_id}/wiki/current`
- `GET /api/v1/companies/{company_id}/knowledge/graph`
- `POST /api/v1/companies/{company_id}/copilot/chat`

## 本番移行時の注意

- `DRY_RUN=false` にする前に、Cost Guard と Release Gate の確認を行います。
- Terraform apply、IAM 変更、Cloud Run deploy は人間の明示承認後に実施します。
- Secret Manager の値をエージェントが直接読み取らない運用を維持します。

## 関連資料

- [デプロイ手順](deploy.md)
- [技術構成サマリ](technical-architecture-summary.md)
- [セキュリティ](security.md)
- [コスト計画](cost-plan.md)
