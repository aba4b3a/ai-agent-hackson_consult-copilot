# インフラ設計

`infra/` は Google Cloud へのデプロイに必要な Terraform、Cloud Build、nginx、Cloud Run 関連設定を管理します。

## 概要

- Terraform は基盤リソースを管理します。
- nginx は static frontend 配信と `/api` / `/agent` の reverse proxy を担当します。
- Cloud Run は nginx / backend / agent の multi-container service を想定します。
- GitHub Actions からは Workload Identity Federation で keyless deploy します。

## フォルダ構成

```text
infra/terraform/   環境別 Terraform と module
infra/nginx/       reverse proxy と frontend 配信用 nginx
infra/cloudbuild/  Cloud Build 設定
```

## 設計方針

### 責務分離

- runtime SA と deploy SA を分離します。
- Terraform による基盤変更と、アプリ image 差し替えを分離します。
- secret value は Secret Manager に置き、リポジトリには置きません。

### 環境独立性

- environment ごとに state と tfvars を分けます。
- `dev` 環境でも production deploy 相当の副作用は人間の承認後に実行します。

## Terraform 手順

```bash
cd infra/terraform/environments/dev
terraform init
terraform plan
terraform apply
```

`terraform apply` は共有インフラ変更のため、人間の明示承認が必要です。

## 新しいリソースの追加

1. 適切な module に resource を追加します。
2. environment 側から module を呼び出します。
3. Cost Guard と IAM の影響を確認します。
4. `terraform plan` の差分をレビューします。
5. 承認後に apply します。

## CI/CD 連携

GitHub Actions deploy は、Artifact Registry へ image を push し、既存 Cloud Run service YAML の image tag を差し替えて `gcloud run services replace` を実行する想定です。
