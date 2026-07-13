# Knowledge Farmer 技術構成サマリ

作成日: 2026-07-12

この文書は、リポジトリ内の実ファイルを確認したうえで、Knowledge Farmer の技術構成、Google Cloud 構成、DevOps 周りの工夫、開発環境、AI 活用、ハーネスエンジニアリングを整理したものです。README や md ファイルだけでなく、Terraform、Docker、Cloud Build、GitHub Actions、FastAPI、ADK Agent、frontend service 実装も確認対象にしています。

## 1. 全体構成

Knowledge Farmer は、中小企業の暗黙知を継続的に収集し、企業ナレッジとして構造化し、月次レポートや追加ヒアリングにつなげる AI エージェント型アプリケーションです。

リポジトリは大きく以下の構成です。

| ディレクトリ | 役割 | 主な技術 |
|---|---|---|
| `front/` | UI | Next.js 16.2.9, React 19.2.7, TypeScript, Tailwind CSS, React Query |
| `back/` | API backend | Python, FastAPI, Pydantic, BigQuery, Cloud Storage, ADK agent client |
| `agent/` | AI agent runtime | Google ADK, multi-agent, BigQuery tools, Storage tools |
| `infra/` | Infrastructure | Terraform, Cloud Run, Artifact Registry, ALB, IAM, Secret Manager, GCS |
| `.github/` | CI/CD | GitHub Actions, reusable AI review workflow, WIF deploy |
| `.ai/overlays/` | Project AI governance | Cost Guard, MCP policy, quality rubric overlay |

## 2. フロントエンド

`front/` は Next.js の static export 構成です。

確認した実装:

- `front/next.config.ts`
  - `output: "export"`
  - `images.unoptimized = true`
- `front/lib/api-client.ts`
  - `NEXT_PUBLIC_API_BASE_URL` を使って FastAPI に接続
  - default は `http://localhost:8000`
- `front/services/*.ts`
  - `/api/v1/companies/...` 配下の API を実際に呼び出す
- `front/hooks/*.ts`
  - React Query 経由で API 呼び出しを画面へ接続
- `front/components/feature/*`
  - Discovery Feed、Research Inbox、Knowledge、Graph、Wiki、Approvals、Monthly Report、Report Copilot などの画面

本番では nginx image の build stage で `front/out` を生成し、nginx から静的配信します。

## 3. バックエンド

`back/` は FastAPI backend です。

確認した実装:

- `back/app/main.py`
  - FastAPI app を作成
  - CORS middleware
  - Tenant auth middleware
  - `/api/v1` router を登録
- `back/app/api/v1/router.py`
  - `companies`
  - `survey`
  - `research`
  - `wiki`
  - `dashboard`
  - `knowledge`
  - `report`
  - `copilot`
  - `approvals`
  - `graph`
  - `bigquery`
  - `schema-validation`
  - `migrations`
  - `observation-signals`

backend は単なる mock API ではなく、BigQuery、Cloud Storage、ADK agent runtime と接続する実装を持っています。

### BigQuery 利用

確認した実装:

- `back/app/db/bigquery.py`
  - production では `google.cloud.bigquery.Client`
  - local では `BIGQUERY_EMULATOR_HOST` 指定時に BigQuery emulator を使用
  - client を process lifetime で cache し、接続 pool の増殖を避ける
- `back/app/crud/bigquery_crud.py`
  - dataset 作成
  - SQL 実行
  - row query
  - JSON row insert
- `back/app/services/bigquery_service.py`
  - company ごとの table name prefix
  - `survey_responses`
  - `knowledge_nodes`
  - `knowledge_edges`
  - BigQuery Property Graph 作成 DDL

### Cloud Storage 利用

確認した実装:

- `back/app/crud/storage_crud.py`
  - `WIKI_BUCKET` がある場合は GCS に読み書き
  - `DRY_RUN` または bucket 未設定時は local filesystem emulator
- `back/app/services/wiki_service.py`
  - `tenants/{company_id}/wiki/current/*`
  - `tenants/{company_id}/wiki/versions/*`
  - current file list / version list / file read

### Agent Runtime 呼び出し

確認した実装:

- `back/app/services/agent_client.py`
  - ADK api server の session 作成
  - `/run` 呼び出し
  - final event から reply を抽出
  - malformed / safety / max token などの terminal finish reason を失敗扱い
- `back/app/services/copilot_service.py`
  - Report Copilot 用に agent runtime へ転送
  - local model の一時失敗を retry
  - tool call JSON が text として返った場合に approval queue へ変換
- `back/app/services/onboarding_service.py`
  - 初期アンケート後に ADK agent を background task として実行
  - stage1 / stage2 に分けて BigQuery table 作成、回答投入、追加質問生成、Wiki 生成を実行
  - agent の自己申告ではなく、GCS 書き込みや BigQuery follow-up 件数を検証して状態遷移

## 4. エージェント実行環境

`agent/` は Google ADK ベースの multi-agent runtime です。

確認した実装:

- `agent/agents/agent.py`
  - `root_agent = orchestrator_agent`
  - `research_agent`
  - `knowledge_agent`
- `agent/tools/bigquery_tools.py`
  - BigQuery dataset / table / graph DDL
  - onboarding answer insert
  - KPI / focus metric candidate insert
  - research follow-up question insert
  - knowledge node / edge upsert
  - custom table DDL proposal
- `agent/tools/storage_tools.py`
  - GCS wiki current / version snapshot write
  - raw answer write
  - derived JSON write
  - research schedule JSON write
- `agent/tools/wiki_tools.py`
  - Wiki / YAML / JSON rendering
- `agent/tools/schema_validator.py`
  - research / knowledge agent output schema validation
- `agent/schemas/*.schema.json`
  - AI output validation schema

設計上の工夫として、`root_agent` には orchestration と一部の基盤 tool のみを持たせ、Wiki write や KPI candidate insert のような分析後の書き込みは `knowledge_agent` に寄せています。コメント上も、root agent が空 content で shortcut 実行することを避ける意図が明記されています。

## 5. Google Cloud 構成

Terraform は `infra/terraform/environments/dev/main.tf` が dev 環境の入口です。

実際に dev 環境から呼ばれている module:

- `project_services`
- `artifact_registry`
- `secret_manager`
- `storage`
- `iam`
- `workload_identity_federation`
- `cloud_run`
- `alb_http`

### Cloud Run

`infra/terraform/modules/cloud_run/main.tf` では、単一 Cloud Run v2 service に3つの container を同居させています。

| container | 役割 | port |
|---|---|---|
| `nginx` | public ingress、static frontend 配信、reverse proxy | 8080 |
| `back` | FastAPI backend | 8000 |
| `agent` | ADK api server | 8081 |

Cloud Run service の ingress は `INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER` です。ALB から Serverless NEG 経由で到達する構成になっています。

### nginx

`infra/nginx/nginx.conf` で以下を実現しています。

- `/` は Next.js static export を配信
- `/api/` は `http://127.0.0.1:8000` の FastAPI へ proxy
- `/agent/` は `http://127.0.0.1:8081` の ADK api server へ proxy
- `/healthz` を軽量 health endpoint として提供

### Artifact Registry の利用

`infra/terraform/modules/artifact_registry` と GitHub Actions deploy workflow で利用します。

本番 deploy では以下の image を build / push します。

- `nginx`
- `back`
- `agent`

### Cloud Storage

`infra/terraform/modules/storage/main.tf` で以下を作成します。

- artifacts bucket
  - 14日で delete する lifecycle rule
- wiki bucket
  - versioning enabled
  - archived object を 90日で NEARLINE、365日で delete

wiki bucket の layout は `agent/tools/storage_tools.py` と対応しています。

例:

```text
tenants/{company_id}/wiki/current/*
tenants/{company_id}/wiki/versions/{timestamp}/*
tenants/{company_id}/raw/fiscal_year={n}/answers/*
tenants/{company_id}/derived/fiscal_year={n}/*
```

### BigQuery

BigQuery は以下の2系統があります。

1. Terraform module
   - `infra/terraform/modules/bigquery/main.tf`
   - common dataset / companies / registry / master / migration history を定義

2. Runtime DDL
   - `back/app/services/bigquery_service.py`
   - `agent/tools/bigquery_tools.py`
   - company ごとの prefix table と Property Graph を作成

注意点として、現時点の `infra/terraform/environments/dev/main.tf` から `bigquery` module は呼ばれていません。実運用上は runtime 側の DDL 実行が中心になっています。

### IAM

`infra/terraform/modules/iam/main.tf` では runtime SA と deploy SA を分離しています。

runtime SA:

- BigQuery dataset dataEditor
- BigQuery jobUser / user
- Storage objectAdmin for wiki / artifacts bucket
- Vertex AI user
- Secret Manager secretAccessor for Gemini API key
- Logging logWriter
- Monitoring metricWriter

deploy SA:

- Cloud Run admin
- Artifact Registry writer
- runtime SA への serviceAccountUser

### Workload Identity Federation

`infra/terraform/modules/workload_identity_federation/main.tf` で GitHub Actions OIDC を構成しています。

- GitHub repository を attribute condition で制限
- deploy SA への `roles/iam.workloadIdentityUser`
- GitHub Actions deploy workflow で `google-github-actions/auth@v2` を使用

### Load Balancer の利用

`infra/terraform/modules/alb_http/main.tf` で External Application Load Balancer を定義しています。

- global address
- Serverless NEG
- backend service
- URL map
- HTTP proxy
- global forwarding rule

現状は HTTP のみで、HTTPS は後から追加できる設計コメントがあります。

## 6. DevOps 周り

### GitHub Actions による CI

`.github/workflows/ci.yaml` で PR 向け CI が定義されています。

jobs:

- `ai-review`
  - `.ai-common` repository の reusable workflow を呼び出し
- `security-check`
  - `.ai-common` repository の reusable workflow を呼び出し
- `front`
  - `npm ci`
  - `npm run lint`
  - `npm run typecheck`
  - `npm run build`
- `back`
  - `uv sync`
  - `ruff check`
  - `mypy app`
  - `pytest`
- `agent`
  - `uv sync`
  - `ruff check`
  - `mypy .`
  - `pytest`

AI review と security check は別リポジトリの共通 workflow を reuse しており、AI 周りの開発標準を横展開できる形になっています。

### GitHub Actions によるデプロイ

`.github/workflows/deploy.yml` で main push / manual dispatch の deploy が定義されています。

特徴:

- WIF で Google Cloud 認証
- Artifact Registry に Docker auth
- commit SHA から image tag を生成
- nginx / back / agent を build / push
- Cloud Run service の YAML を取得し、3 container の image を patch
- `gcloud run services replace` で multi-container Cloud Run service を更新

`gcloud run deploy` では sidecar container image をまとめて扱いづらいため、YAML を patch して replace する構成になっています。

### Cloud Build

`infra/cloudbuild/` に Cloud Build 設定もあります。

- `cloudbuild-pr.yaml`
  - front lint/typecheck
  - back ruff/mypy/pytest
  - agent ruff/mypy/pytest
- `cloudbuild.yaml`
  - front build
  - back / agent image build and push
  - back / agent を Cloud Run service として deploy

注意点として、`cloudbuild.yaml` は back / agent の個別 Cloud Run service deploy で、現在の GitHub Actions deploy の multi-container Cloud Run service とは構成が異なります。本命は `.github/workflows/deploy.yml` 側に見えます。

### PR テンプレート

`.github/pull_request_template.md` は `.ai-common` 生成物で、以下を PR 品質ゲートとして要求しています。

- 品質エビデンス
- Playwright UI review
- AI 品質評価
- Security review
- Cost Guard 判定
- Release Gate
- secret / PII 混入なし
- production deploy / IAM update / terraform apply なし

## 7. 開発環境

### Docker Compose

`docker-compose.yaml` は profile で用途を分けています。

#### `dev` profile

```bash
docker compose --profile dev up
```

起動するもの:

- `front`
  - Next dev server
  - port 3000
- `back`
  - FastAPI
  - port 8000
- `agent`
  - ADK api server
  - port 8080
- `bigquery-emulator`
  - port 9050
- `ollama`
  - port 11434
- `devcontainer`

#### `sidecar` profile

```bash
docker compose --profile sidecar up
```

Cloud Run multi-container の再現用です。

- nginx が唯一の public port 8080
- back / agent は `network_mode: "service:nginx"` で nginx と network namespace を共有
- Cloud Run の localhost sidecar 構成に近い状態を local で検証可能

確認例:

```bash
curl http://localhost:8080/
curl http://localhost:8080/api/v1/health
curl http://localhost:8080/agent/list-apps
```

### Dev Container の利用

`.devcontainer/devcontainer.json` では以下を整備しています。

- Docker outside-of-Docker
- Terraform
- Python 3.12
- BigQuery emulator / Ollama を runServices として起動
- VS Code extensions
  - Python
  - mypy
  - ruff
  - ESLint
  - Tailwind CSS
  - Playwright
  - Terraform
  - Cloud Code
  - GitHub Actions
  - Containers
- `postCreateCommand`
  - `python -m pip install --user uv && make setup`

### Makefile

`Makefile` で主要操作が標準化されています。

- `make dev`
- `make sidecar`
- `make lint`
- `make terraform-check`
- `make test`
- `make seed-emulator`
- `make build`
- `make clean`

## 8. AI 活用

### Multi-agent 設計

`agent/agents/agent.py` で以下を定義しています。

- `orchestrator_agent`
  - 全体進行
  - tool 実行順序制御
  - Research / Knowledge agent への handoff
- `research_agent`
  - 追加質問生成
  - 初期アンケート / follow-up question
- `knowledge_agent`
  - 暗黙知抽出
  - KPI / focus metric 候補
  - knowledge node / edge
  - Wiki rendering
  - GCS / BigQuery 書き込み

### マルチエージェント設計

BigQuery tools:

- dataset / table 作成
- Property Graph 作成
- answer event insert
- KPI / focus metric candidate insert
- follow-up question insert
- knowledge node / edge upsert
- human approval required な DDL proposal

Storage tools:

- raw answer 保存
- derived JSON 保存
- wiki current 保存
- wiki version snapshot 保存
- research schedule 登録

Wiki tools:

- company profile
- KPI definitions
- focus metrics
- research policy
- manifest
- custom table update

### エージェントツール

AI が出した候補をそのまま確定せず、approval queue を通す設計があります。

確認した実装:

- `back/app/services/approval_service.py`
- `back/app/api/v1/endpoints/approvals.py`
- `front/components/feature/approvals/ApprovalsList.tsx`
- `agent/tools/bigquery_tools.py`
  - `upsert_current_kpi_definition`
  - `upsert_current_focus_metric_definition`
  - `approved=True` でないと更新しない

### 人間参加型の承認

AI output の validation 用に以下があります。

- `agent/tools/schema_validator.py`
- `agent/schemas/research_agent_output.schema.json`
- `agent/schemas/knowledge_agent_output.schema.json`

AI 出力を downstream decision に使う前提で、schema-valid を求める運用標準と整合しています。

## 9. 共通 AI コンポーネント

`.gitmodules` で `.ai-common` が別 repository として定義されています。

```text
path = .ai-common
url = https://github.com/aba4b3a/ai-agent-hackason_ai-common
```

また `.github/workflows/ci.yaml` では、共通 repository の reusable workflow を呼び出しています。

```yaml
ai-review:
  uses: aba4b3a/ai-agent-hackason_ai-common/.github/workflows/ai-review.yml@...

security-check:
  uses: aba4b3a/ai-agent-hackason_ai-common/.github/workflows/security-check.yml@...
```

このため、AI review、security check、PR template、agent operating standard などを別 repository の共通コンポーネントとして管理し、複数 project に展開する前提の構成です。

現作業ツリーでは `.ai-common` directory 本体は未チェックアウトでした。一方で `.ai/overlays` には project 固有 overlay が存在し、共通標準を project 向けに tighten する形になっています。

## 10. ハーネスエンジニアリング

この repository では、AI agent を単に呼び出すだけではなく、失敗しやすい外部依存や LLM 実行を検証可能にする harness が複数あります。

### スキーマ検証

- BigQuery emulator
- filesystem storage emulator
- Ollama
- Docker Compose dev profile
- Docker Compose sidecar profile
- devcontainer

### Cloud Run 再現ハーネス

`docker compose --profile sidecar` により、本番 Cloud Run の multi-container localhost 共有を再現できます。

これは以下の検証に使えます。

- nginx の path routing
- static frontend 配信
- `/api` backend routing
- `/agent` ADK routing
- Cloud Run の single ingress + sidecar 構成

### エージェント信頼性ハーネス

`back/app/services/onboarding_service.py` は、agent の自然言語応答だけを成功判定にしていません。

実際の副作用を検証します。

- GCS wiki file が run 開始後に更新されたか
- BigQuery follow-up question event が生成されたか
- stage1 / stage2 の状態遷移
- retry 時に過去 run の成果物を誤判定しないよう timestamp を見る

この設計は、LLM が「成功した」と文章で返しても実際には tool を呼んでいないケースを検出するための harness engineering です。

### テストハーネス

- backend pytest
  - onboarding
  - survey template
  - monthly report
  - knowledge extraction
  - graph API
  - health
- agent pytest
  - scoring
  - continuous discovery tools
- frontend Playwright
  - dashboard
  - graph

### 品質・リリース判定ハーネス

- `agent/eval/golden_cases/sample_quality_run.json`
- `agent/eval/rubrics/quality_rubric.md`
- `.ai/overlays/skills/project-quality-rubric/SKILL.md`
- `.github/pull_request_template.md`

ただし、以下は現時点で placeholder 的です。

- `agent/agents/quality_eval_agent.py`
- `agent/agents/cost_guard_agent.py`
- `agent/agents/release_gate_agent.py`

project overlay にも、これらを本体 agent と誤認しないよう注意が書かれています。

## 11. コストガードと安全性

Cost Guard の枠組みはあります。

確認したファイル:

- `.ai/overlays/COST_GUARD.project.md`
- `.github/pull_request_template.md`
- `agent/agents/cost_guard_agent.py`

ただし、project overlay の具体値は未記入です。

未記入例:

- 月次上限
- Cloud Run max
- Cloud Build 分数上限
- Cloud Storage TB-month
- Firestore read/write
- AI 呼び出し token 上限

インフラ側では Cloud Run の `min_instance_count` / `max_instance_count` や Cloud Build / deploy の分離により、コスト制御を意識しています。

## 12. 注意点 / 現状のギャップ

確認できた注意点です。

1. `infra/terraform/modules/bigquery` は存在するが、`infra/terraform/environments/dev/main.tf` では未接続。
2. `infra/terraform/modules/budget` は placeholder。
3. `infra/terraform/modules/firestore` / `research_dispatch` は存在するが、dev 環境では未接続。
4. `infra/cloudbuild/cloudbuild.yaml` は back / agent 個別 Cloud Run deploy で、GitHub Actions の multi-container deploy と方式が違う。
5. `.ai-common` は submodule として定義されているが、現作業ツリーには本体 directory が存在しなかった。
6. `agent/agents/*_guard/eval/release` 系は placeholder 実装で、本番配線された中核 agent ではない。
7. frontend E2E の一部は旧 UI 文言に依存しており、Knowledge Farmer 文言変更後は更新が必要。

## 13. 提出向け要約

Knowledge Farmer は、Next.js static frontend、FastAPI backend、Google ADK multi-agent runtime を、Cloud Run multi-container service として構成した AI Agent アプリケーションです。

Google Cloud では、Cloud Run、Artifact Registry、Cloud Storage、BigQuery、Vertex AI、Secret Manager、Application Load Balancer、Workload Identity Federation を利用します。nginx を ingress container とし、同一 Cloud Run instance 内の FastAPI と ADK agent に localhost proxy することで、frontend、API、agent runtime を単一サービスとして運用できます。

DevOps 面では、GitHub Actions による CI/CD、WIF による keyless deploy、Artifact Registry への image push、Cloud Run service YAML patch による multi-container deploy、Terraform による基盤管理を備えています。さらに `.ai-common` を別 repository の共通 AI 開発基盤として使い、AI review、security check、PR template、Cost Guard、Release Gate の考え方を再利用できる設計です。

AI 活用面では、ADK の orchestrator / research / knowledge agent が、追加質問生成、暗黙知抽出、BigQuery Graph 用 node / edge 生成、Wiki 生成、月次レポートや Copilot の材料化を担います。AI の出力はそのまま確定せず、schema validation と human-in-the-loop approval を前提にしています。

ハーネスエンジニアリングとして、BigQuery emulator、filesystem storage emulator、Ollama、Cloud Run sidecar reproduction、Playwright E2E、pytest、agent output schema、実 side effect による agent 成功判定が整備されています。これにより、LLM の自然言語上の自己申告ではなく、GCS や BigQuery に実際に成果物が残ったかを検証しながら、継続的なナレッジ形成ループを運用できる構成になっています。
