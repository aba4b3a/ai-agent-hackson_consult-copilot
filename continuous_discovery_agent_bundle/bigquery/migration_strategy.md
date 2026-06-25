# BigQuery Migration Strategy

## MVP推奨

最初は「SQLファイル + schema_migration_history + Cloud Build/手動スクリプト」で十分。

## ルール

1. DDLはGit管理する
2. ファイル名は `V001__description.sql` の形式
3. 共通データセット用と企業別テンプレート用を分ける
4. 適用済みマイグレーションは `cd_common.schema_migration_history` に記録
5. 企業別データセット作成時は `tenant_template` のDDLを `{TENANT_DATASET}` に置換して適用
6. 破壊的変更は原則禁止。列追加はNULLABLEで行う
7. 大きな変更は新テーブル作成 + データ移行 + View切替で対応

## 将来案

- Dataform: current_* や snapshot などの変換処理管理に使う
- Terraform: dataset/IAM/bucket/lifecycleのIaC化に使う
- Liquibase/Flyway: 既存のDBマイグレーション文化がある場合のみ検討
