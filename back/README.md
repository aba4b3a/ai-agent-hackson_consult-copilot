# バックエンド設計

`back/` は Consult Copilot の FastAPI backend です。画面向け API、BigQuery / Cloud Storage 連携、agent runtime 呼び出し、レポート生成、承認フローを担当します。

## 概要

- `api/v1/` は HTTP endpoint と request / response の境界です。
- `services/` は業務ロジックです。
- `crud/` は BigQuery や Cloud Storage など永続化先との入出力です。
- `schemas/` は Pydantic 型です。
- `main.py` で middleware と router を組み立てます。

## フォルダ構成

```text
app/api/v1/      endpoint と router
app/services/    業務ロジック
app/crud/        永続化層
app/schemas/     Pydantic schema
app/db/          BigQuery client など
app/storage_seed ローカル seed data
```

## 依存関係の方向

```text
api -> services -> crud / db / external client
```

endpoint から直接 BigQuery や GCS を触らず、service 経由にします。

## サービス実装ルール

- endpoint は入力検証と service 呼び出しに集中します。
- service は業務上の状態遷移と side effect の確認を担当します。
- AI agent の最終テキストだけで成功判定せず、BigQuery / GCS の実 side effect を確認します。
- downstream decision に使う AI 出力は schema validation を通します。

## Report API

`GET /api/v1/companies/{company_id}/report/monthly` は、前月分の Monthly Discovery Report を取得します。

1. `tenants/{company_id}/reports/monthly/{YYYY-MM}/report.json` を Cloud Storage または local storage emulator から探します。
2. 存在する場合は保存済み JSON を返します。
3. 存在しない場合は BigQuery または seed data から生成し、同じ path に保存して返します。

## ローカル開発

```bash
uv sync
uv run ruff check app
uv run mypy app
uv run pytest
```

通常はリポジトリルートから Makefile を使います。

```bash
make setup
make dev
make test
```

## BigQuery Emulator

ローカルでは `BIGQUERY_EMULATOR_HOST` が設定されている場合に emulator へ接続します。

```text
PROJECT_ID=local-project
BQ_DATASET_PREFIX=consultant_copilot
BIGQUERY_EMULATOR_HOST=http://bigquery-emulator:9050
```

注意点:

- 本物の BigQuery に接続しないことをログと環境変数で確認します。
- seed data と emulator data の前提がずれる場合は、対象 company_id を確認します。
- production 相当では emulator を無効化し、権限と Cost Guard を確認します。
