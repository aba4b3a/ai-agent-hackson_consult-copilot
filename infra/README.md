# Infrastructure Architecture

## 概要
本プロジェクトのインフラ環境は、Terraformによるコード管理 (IaC) および Google Cloud Build によるCI/CDパイプラインを採用しています。再利用性を高めるため、リソース単位でモジュール化したアーキテクチャを採用しています。

## フォルダ構成と役割

```text
├── cloudbuild/      # CI/CDパイプライン定義
├── firebase/        # Firebase Hosting 設定
├── scripts/         # メンテナンス用補助スクリプト
└── terraform/       # Google Cloud インフラ定義
    ├── environments/# 環境ごとの実行ディレクトリ (dev, prod)
    └── modules/     # リソースごとの定義 (artifact_registry, cloud_run, etc.)
```

---

## インフラ構成の指針

### 1. 責務の分離
- **`modules/` (部品)**:
  各リソースの設定（Terraformの定義）のみを記述します。ここで定義されたモジュールは複数の環境から呼び出されます。
- **`environments/` (実体)**:
  各環境（dev/prod）の構成を管理します。`modules/` を読み込み、環境固有の変数（プロジェクトID、インスタンスサイズ等）を注入します。

### 2. 環境の独立性
`dev` と `prod` は物理的にディレクトリが分かれています。`terraform apply` を実行する際は、必ず対象の環境ディレクトリ内に移動してから実行してください。

---

## 開発・運用ガイド

### 1. Terraform 適用手順
各環境ディレクトリで以下の操作を行います。

```bash
# 1. 目的の環境へ移動
cd terraform/environments/dev

# 2. 初期化 (初回またはモジュール変更時)
terraform init

# 3. 計画確認
terraform plan

# 4. 適用
terraform apply
```

### 2. 新しいリソースの追加方法
1.  `terraform/modules/` 配下に新しいモジュール用ディレクトリを作成します。
2.  `main.tf`（および必要に応じて `variables.tf`, `outputs.tf`）を定義します。
3.  `environments/` の各ディレクトリにある `main.tf` で、作成したモジュールを呼び出します。

### 3. 注意点
- **State管理**: Stateファイルはリモートバックエンド（GCS）で管理してください。
- **機密情報**: APIキーやパスワードなどの機密情報は、コードに直書きせず、`secret_manager` モジュールを使用して管理してください。
- **最小権限**: IAM設定 (`modules/iam`) を変更する場合は、そのリソースに必要な最小限の権限のみを付与するように徹底してください。

---

## CI/CD 連携
- **PR時 (`cloudbuild-pr.yaml`)**: `terraform plan` を実行し、変更の影響を確認します。
- **マージ時 (`cloudbuild.yaml`)**: `terraform apply` を実行し、本番環境または開発環境へ変更を反映させます。
