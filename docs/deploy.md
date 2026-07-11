# Deploy Runbook — Cloud Run (sidecar) + ALB

このドキュメントは、front(静的エクスポート) / back(FastAPI) / agent(ADK) を **1 つの Cloud Run サービスに 3 コンテナのサイドカー構成でデプロイ** し、公開入口は **External HTTP(S) Application Load Balancer(ALB)** のみに限定する運用手順です。

---

## 1. 構成の全体像

```text
Browser
  │  HTTP (後日 HTTPS 化予定)
  ▼
[ External ALB (global) ]  ── パブリックIP唯一の入口
  │  Serverless NEG
  ▼
[ Cloud Run v2 service: consult-copilot-app ]
  │  ingress = INTERNAL_LOAD_BALANCER (run.app 直叩きは 403)
  │
  ├── (ingress) nginx    :8080  ── front 静的配信 + /api → :8000, /agent → :8081
  ├── (sidecar) back     :8000  ── FastAPI
  └── (sidecar) agent    :8081  ── ADK api_server
        │
        └── Vertex AI (Gemini) / BigQuery / Cloud Storage (llm-wiki)
            にランタイム SA 経由でアクセス
```

**共通プレフィックス**: `consult-copilot`(`var.service_prefix` で変更可)。

**リソース命名例**
- Cloud Run: `consult-copilot-app`
- Artifact Registry: `consult-copilot`
- Runtime SA: `consult-copilot-runtime@<project>.iam.gserviceaccount.com`
- Deploy SA: `consult-copilot-deploy@<project>.iam.gserviceaccount.com`
- ALB IP: `consult-copilot-alb-ip`
- WIF Pool: `consult-copilot-gha`

---

## 2. 前提と既存リソース

**既に用意されている前提**:
- GCP プロジェクトが存在し、Billing が有効。
- BigQuery データセット `consultant_copilot` (と関連テーブル) が作成済み。Terraform では **触りません**(IAM 付与のみ)。

**Terraform で新規作成するもの**:
- Cloud Run 用 API 群の有効化(`project_services` モジュール)
- Artifact Registry リポジトリ
- 2 つの GCS バケット (`<project>-consult-copilot-artifacts`, `<project>-consult-copilot-wiki`)
- Secret Manager: `consult-copilot-gemini-api-key`(値は後述の手順で手動投入)
- ランタイム SA + デプロイ SA + 必要 IAM ロール
- Workload Identity Federation Pool/Provider(GitHub Actions 用)
- Cloud Run v2 サービス(サイドカー3コンテナ)
- External ALB(HTTP)

---

## 3. 初回準備(手動作業)

以下は **1 回だけ、人間の手で** 実施します。Terraform を実行する前提条件です。

### 3.1 gcloud のセットアップ

```powershell
gcloud auth login
gcloud auth application-default login
gcloud config set project <YOUR_PROJECT_ID>
```

### 3.2 tfstate 用 GCS バケットを作成

Terraform の state を GCS で管理します。バケットは chicken-and-egg なので手作業で先に作ります。

```powershell
$PROJECT_ID = "<YOUR_PROJECT_ID>"
$PREFIX = "consult-copilot"
$STATE_BUCKET = "$PROJECT_ID-$PREFIX-tfstate"

gcloud storage buckets create "gs://$STATE_BUCKET" `
    --location=asia-northeast1 `
    --uniform-bucket-level-access `
    --project=$PROJECT_ID

# 万が一の巻き戻しに備えバージョニング推奨
gcloud storage buckets update "gs://$STATE_BUCKET" --versioning
```

### 3.3 `terraform.tfvars` を作成(コミットしない)

```powershell
cd infra/terraform/environments/dev
Copy-Item terraform.tfvars.example terraform.tfvars
# 手で編集:
#   project_id        = "..."
#   github_repository = "your-org/your-repo"
```

### 3.4 初回 `terraform init`(state バックエンド指定)

`providers.tf` は state バケット名をコードに書かず、`-backend-config` で渡します。

```powershell
terraform init -backend-config="bucket=$STATE_BUCKET"
```

以降 `terraform init` を再実行する場合も同じ `-backend-config` を渡してください(または `.terraform/backend-override.tf` を作成)。

### 3.5 Gemini API Key(必要な場合のみ)

Vertex AI(ADK ネイティブ統合)を使う場合、`GOOGLE_GENAI_USE_VERTEXAI=TRUE` で SA 経由の認証になるため API Key は不要です。もし外部 Gemini API を併用する場合のみ、Terraform 適用後に値を投入します:

```powershell
$KEY = Read-Host -AsSecureString "Enter Gemini API Key"
# ... 手動で Secret Manager に投入(手順割愛)
```

---

## 4. パターン A: 手動 Terraform デプロイ

インフラ全体を Terraform 単独で完結させる手順です。**アプリの新機能追加(コード変更)を伴わない、インフラ初回セットアップやパラメータ変更時に使います。**

### 4.1 プラン確認

```powershell
cd infra/terraform/environments/dev
terraform plan -out=tfplan
```

差分の主なリソース:
- APIs 有効化(10 個ほど)
- Artifact Registry
- SA × 2 + IAM バインディング
- GCS バケット × 2
- Secret Manager × 1
- Cloud Run サービス(初期状態は `hello world` イメージ)
- ALB 一式(static IP、NEG、backend service、URL map、forwarding rule)
- WIF Pool/Provider

### 4.2 適用

```powershell
terraform apply tfplan
```

完了すると outputs に以下が出ます(GitHub Actions 側で使います):

```text
alb_ip_address              = "34.x.x.x"
cloud_run_service_name      = "consult-copilot-app"
deploy_sa_email             = "consult-copilot-deploy@<project>.iam.gserviceaccount.com"
workload_identity_provider  = "projects/<num>/locations/global/workloadIdentityPools/consult-copilot-gha/providers/github"
wiki_bucket                 = "<project>-consult-copilot-wiki"
```

### 4.3 動作確認(hello world)

```powershell
$ALB_IP = (terraform output -raw alb_ip_address)
curl "http://$ALB_IP/"
# → "It's running!" のようなレスポンス(hello イメージ)。
```

> ALB のバックエンド有効化 (health check の伝搬) に 3〜5 分かかることがあります。

### 4.4 アプリコンテナの初回ビルド & デプロイ(手動)

手動で 3 つのイメージを作って Cloud Run に反映します。以降は GitHub Actions に任せる想定です。

```powershell
$PROJECT_ID = (terraform output -raw ... ) # 実際は tfvars を参照
$REGION = "asia-northeast1"
$REPO = "consult-copilot"
$SHA = "bootstrap"
$BASE = "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO"

# 認証
gcloud auth configure-docker "$REGION-docker.pkg.dev" --quiet

# nginx (front を焼き込む)
docker build -t "$BASE/nginx:$SHA" -f infra/nginx/Dockerfile .
docker push "$BASE/nginx:$SHA"

# back
docker build -t "$BASE/back:$SHA" -f back/Dockerfile back
docker push "$BASE/back:$SHA"

# agent
docker build -t "$BASE/agent:$SHA" -f agent/Dockerfile agent
docker push "$BASE/agent:$SHA"

# Cloud Run の 3 コンテナの image を差し替え
gcloud run services describe consult-copilot-app --region $REGION --format=export > service.yaml
# service.yaml 内の 3 つの `image:` を上記 tag に手で置き換えるか、
# .github/workflows/deploy.yml 内の python スクリプトを流用してください。
gcloud run services replace service.yaml --region $REGION
```

### 4.5 動作確認(実アプリ)

```powershell
curl "http://$ALB_IP/api/v1/healthz"        # back
curl "http://$ALB_IP/agent/"                # agent
Start-Process "http://$ALB_IP/"             # ブラウザで front
```

---

## 5. パターン B: GitHub Actions での自動デプロイ

`main` ブランチにマージすると、自動でイメージビルド〜Cloud Run 反映まで行います。**アプリのコード変更のリリースはこちら** を使います。

### 5.1 GitHub Secrets の登録

Terraform 適用後の outputs を使い、GitHub リポジトリの **Settings → Secrets and variables → Actions** に以下 3 つを登録します:

| Secret 名 | 値 |
| --- | --- |
| `GCP_PROJECT_ID` | `<YOUR_PROJECT_ID>` |
| `GCP_DEPLOY_SA_EMAIL` | `terraform output -raw deploy_sa_email` の値 |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | `terraform output -raw workload_identity_provider` の値 |

> WIF は SA JSON キーを一切扱わないので、リポジトリに秘匿情報を置く必要がありません。

### 5.2 ワークフローの動き

`.github/workflows/deploy.yml` は以下を行います:

1. `google-github-actions/auth@v2` で OIDC → デプロイ SA へトークン交換。
2. Artifact Registry に Docker 認証。
3. 3 つのイメージを `docker build` & `push`。
   - `nginx`: リポジトリルートを context に、`infra/nginx/Dockerfile` でビルド(front を静的ビルドして焼き込み)。
   - `back`: `back/` を context に。
   - `agent`: `agent/` を context に。
4. `gcloud run services describe --format export` で service YAML を取得し、python で 3 コンテナの `image` を差し替え、`gcloud run services replace` で適用。
5. Job summary にデプロイ結果を出力。

タグは `$GITHUB_SHA` の先頭 12 文字を使用します。

### 5.3 手動トリガ

Actions タブ → `deploy` → `Run workflow` で任意ブランチから起動できます(コード変更なしの再デプロイ用)。

---

## 6. 補足: セキュリティと設計上のポイント

### 6.1 なぜ ingress を `INTERNAL_LOAD_BALANCER` にしているか

Cloud Run サービスに割り当てられる `*.run.app` の URL を直接叩かれると ALB(と Cloud Armor / 将来の WAF)を経由しません。`INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER` にすることで、外部からは **ALB 経由のリクエストのみ許可** されます。`allUsers` に付けている `roles/run.invoker` は、ALB からのリクエストが認証情報を持たないことに対応するためで、ingress 制限と組み合わせることで公開範囲が ALB に限定されます。

### 6.2 なぜサイドカー3コンテナか

- 1 インスタンスで 3 プロセスが同居するため、`min_instances=0` の恩恵を最大化(アイドル課金ゼロ)。
- ブラウザから見て同一オリジンで完結し、CORS 不要。
- Cold start が 3 サービス分に分散せず 1 回で済む。

### 6.3 ランタイム SA の権限(最小権限)

- `roles/bigquery.dataEditor` on `dataset:consultant_copilot`(データセット限定)
- `roles/bigquery.jobUser` on project(クエリ課金プロジェクトの制約)
- `roles/storage.objectAdmin` on `<project>-consult-copilot-wiki` / `-artifacts`
- `roles/aiplatform.user`(Vertex AI Gemini)
- `roles/secretmanager.secretAccessor` on `consult-copilot-gemini-api-key`
- `roles/logging.logWriter`, `roles/monitoring.metricWriter`

### 6.4 デプロイ SA の権限

- `roles/run.admin`
- `roles/artifactregistry.writer`
- ランタイム SA に対する `roles/iam.serviceAccountUser`

### 6.5 Terraform とアプリ更新の分離

Cloud Run のコンテナ image は CI が更新します。Terraform 側では `lifecycle.ignore_changes` で 3 つのコンテナの `image` フィールドを無視するようにしてあり、`terraform apply` が CI の更新を巻き戻すことはありません。

### 6.6 後日 HTTPS 化するときの追加作業(要ドメイン)

1. ドメインを取得し、DNS の A レコードを `alb_ip_address` に向ける。
2. `modules/alb_http` に以下を追加(将来対応):
   - `google_compute_managed_ssl_certificate`(`managed.domains = [var.alb_domain]`)
   - `google_compute_target_https_proxy`
   - `google_compute_global_forwarding_rule`(port 443)
   - 既存 HTTP 側は 443 へリダイレクトする `url_map` に差し替え。
3. 変数 `enable_https = true` / `alb_domain = "app.example.com"` を渡して `terraform apply`。

---

## 7. トラブルシュート

| 症状 | 原因 | 対処 |
| --- | --- | --- |
| ALB IP に curl して 502 が延々続く | Cloud Run が listen していない / startup probe 失敗 | `gcloud run services logs read consult-copilot-app --region asia-northeast1` で 3 コンテナのログ確認。特に agent の `--port 8081` オーバーライドが効いているか。 |
| Cloud Run で "PORT is not open" | ingress コンテナが port 8080 で listen していない | `infra/nginx/nginx.conf` の `listen 8080` を確認、`Dockerfile` の `EXPOSE 8080`。 |
| BigQuery `Permission denied` | ランタイム SA の dataset バインドが未反映 | `terraform apply` 再実行 → `gcloud asset search-all-iam-policies` で確認。 |
| `WIKI_BUCKET is required` エラー | back/agent に `WIKI_BUCKET` env var が渡っていない | `modules/cloud_run/main.tf` の env 定義を確認。 |
| GitHub Actions が `Permission 'iam.serviceAccounts.getAccessToken' denied` | WIF の attribute_condition が repo と一致していない | `terraform.tfvars` の `github_repository` を修正、`terraform apply`。 |
| `terraform apply` が Cloud Run の image を毎回変えようとする | lifecycle ignore が効いていない | `modules/cloud_run/main.tf` の `ignore_changes` を確認。 |

---

## 8. 破棄(注意)

**開発環境の破棄は明示的に人間が実行してください**。特に GCS バケット、Cloud Run、ALB IP は破棄されると再取得できない(IP)/データ喪失(GCS)のリスクがあります。

```powershell
cd infra/terraform/environments/dev
terraform plan -destroy
# 内容確認の上、慎重に:
terraform destroy
```

BigQuery データセットは Terraform 管理外なので destroy では消えません。
