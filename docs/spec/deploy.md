# デプロイ手順: Cloud Run sidecar + ALB

この手順は、nginx / backend / agent を 1 つの Cloud Run service に載せ、Application Load Balancer から到達させる構成を前提にします。production deploy、Terraform apply、IAM 変更は必ず人間の明示承認を得てから実行してください。

## 1. 全体構成

- `nginx`: public ingress、静的 frontend 配信、`/api` と `/agent` の reverse proxy
- `back`: FastAPI backend
- `agent`: Google ADK api_server
- `Artifact Registry`: 3 コンテナイメージの保存先
- `Cloud Run`: multi-container service
- `Application Load Balancer`: 外部公開入口
- `Secret Manager`: Gemini API key などの秘密情報
- `Workload Identity Federation`: GitHub Actions からの keyless deploy

## 2. 前提

現状の `infra/terraform/environments/dev` は Artifact Registry 以外の module 呼び出しが未接続です。Cloud Run、IAM、Secret Manager、Storage、BigQuery などを Terraform から適用する場合は、module 接続を追加して plan を確認してから進めます。

- Google Cloud project が作成済み
- `gcloud` が対象 project を向いている
- Terraform state 用 GCS bucket を作成済み、または作成する権限がある
- Artifact Registry、Cloud Run、Secret Manager などの API を有効化できる
- GitHub Actions deploy を使う場合は GitHub repository 名が確定している

## 3. 初回準備

### gcloud の設定

```bash
gcloud auth login
gcloud config set project <PROJECT_ID>
gcloud auth application-default login
```

### tfstate 用 GCS bucket

```bash
gcloud storage buckets create gs://<TFSTATE_BUCKET> --location=asia-northeast1
gcloud storage buckets update gs://<TFSTATE_BUCKET> --versioning
```

### terraform.tfvars

`infra/terraform/environments/dev/terraform.tfvars` を作成します。このファイルはコミットしません。

```hcl
project_id        = "<PROJECT_ID>"
region            = "asia-northeast1"
github_repository = "<OWNER>/<REPO>"
```

### Terraform init

```bash
cd infra/terraform/environments/dev
terraform init \
  -backend-config="bucket=<TFSTATE_BUCKET>" \
  -backend-config="prefix=consult-copilot/dev"
```

### Secret Manager

Gemini API key などが必要な場合は、人間が Secret Manager に登録します。エージェントは secret value を読み取りません。

## 4. 手動 Terraform デプロイ

### plan

```bash
terraform plan
```

### apply

`terraform apply` は共有インフラへ副作用があるため、人間の承認後に実行します。

```bash
terraform apply
```

### 初期動作確認

Cloud Run が hello image などで起動している段階では、ALB または service URL で疎通だけ確認します。

```bash
curl http://<ALB_IP>/healthz
```

## 5. アプリコンテナのビルドと反映

Artifact Registry へ認証します。

```bash
gcloud auth configure-docker <REGION>-docker.pkg.dev
```

各イメージを build / push します。

```bash
docker build -t <REGION>-docker.pkg.dev/<PROJECT_ID>/<REPOSITORY>/nginx:<SHA> -f infra/nginx/Dockerfile .
docker build -t <REGION>-docker.pkg.dev/<PROJECT_ID>/<REPOSITORY>/back:<SHA> back
docker build -t <REGION>-docker.pkg.dev/<PROJECT_ID>/<REPOSITORY>/agent:<SHA> agent

docker push <REGION>-docker.pkg.dev/<PROJECT_ID>/<REPOSITORY>/nginx:<SHA>
docker push <REGION>-docker.pkg.dev/<PROJECT_ID>/<REPOSITORY>/back:<SHA>
docker push <REGION>-docker.pkg.dev/<PROJECT_ID>/<REPOSITORY>/agent:<SHA>
```

既存の Cloud Run service YAML を取得し、3 つの container image を差し替えて replace します。

```bash
gcloud run services describe <SERVICE_NAME> --region <REGION> --format export > service.yaml
# service.yaml の image を差し替える
gcloud run services replace service.yaml --region <REGION>
```

## 6. GitHub Actions デプロイ

`.github/workflows/deploy.yml` は次の流れを想定します。

1. GitHub Actions OIDC で Google Cloud に認証
2. Artifact Registry へ Docker login
3. `nginx` / `back` / `agent` の 3 image を build
4. Artifact Registry へ push
5. 既存 Cloud Run service YAML を取得
6. image tag を commit SHA に差し替え
7. `gcloud run services replace` で更新

必要な GitHub Secrets や Variables は、secret value を露出しない形で人間が登録します。

## 7. セキュリティ上の設計

- Cloud Run ingress は `INTERNAL_LOAD_BALANCER` を使い、外部入口は ALB に寄せます。
- GitHub Actions には長期サービスアカウントキーを置かず、Workload Identity Federation を使います。
- runtime SA と deploy SA を分離します。
- Terraform は基盤管理、アプリ更新は image 差し替えとして分離します。
- HTTPS 化にはドメイン、証明書、ALB 設定の追加が必要です。

## 8. トラブルシュート

- Cloud Run が起動しない場合は、各 container の port と health check を確認します。
- `/api` が 404 になる場合は nginx の routing と backend の root path を確認します。
- `/agent` が失敗する場合は ADK api_server の port と `AGENT_BASE_URL` を確認します。
- Artifact Registry push に失敗する場合は repository 名、region、Docker auth を確認します。
- GitHub Actions 認証に失敗する場合は WIF provider の attribute condition と repository 名を確認します。

## 9. 破棄

`terraform destroy` は共有インフラを削除する破壊的操作です。実行前に対象 project、state、削除対象を人間が確認してください。

```bash
terraform plan -destroy
terraform destroy
```
