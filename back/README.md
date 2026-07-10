# Backend Architecture

## 概要
本プロジェクトは、FastAPIを使用したバックエンドアプリケーションです。
メンテナンス性とテスト容易性を高めるため、レイヤードアーキテクチャを採用しています。

## フォルダ構成と責務
各ディレクトリは以下の責務を持ちます。

```text
app/
├── api/          # API層: HTTPリクエストの受け取り、エンドポイント定義
├── core/         # 設定: 環境変数、共通設定、セキュリティ設定
├── crud/         # DBアクセス層: データベースへのクエリ発行のみを担当
├── db/           # インフラ層: DB接続設定、セッション管理
├── schemas/      # データ型定義: Pydanticモデルによるバリデーション
├── services/     # ビジネスロジック層: 複雑な業務処理、外部APIクライアント
└── utils/        # ユーティリティ: 汎用的なヘルパー関数
```

---

## 開発ルールとアーキテクチャ

### 1. 依存関係の方向
以下の順序で呼び出しを行ってください。**逆方向の呼び出しは禁止です。**

> `api/` → `services/` → `crud/` → `db/`

*   **API層 (`api/`)**: `services/` のメソッドを呼び出し、リクエストのパースとレスポンスの変換を行います。
*   **ビジネスロジック (`services/`)**: 業務上のルールを実装します。複数のサービスやCRUDを組み合わせることができます。
*   **DBアクセス (`crud/`)**: データの取得・保存のみを担当します。

### 2. サービス間の呼び出し
*   サービス間（例: `UserService` から `EmailService` を呼ぶ）の相互呼び出しは許可しますが、**「循環参照」**には注意してください。
*   循環参照が発生する場合は、共通のロジックをより下位のレイヤー（`utils/` や共通サービス層`services/common/`）に切り出してください。

### 3. データ型の利用
*   `api/` 層での入力・出力には `schemas/` を使用してください。
*   `services/` 層以下では、必要に応じてDBモデルや、`schemas/` で定義したDTO（Data Transfer Object）を使用します。

---

## 実装ガイドライン

### エンドポイントの作成方法 (`api/v1/`)
```python
from fastapi import APIRouter, Depends
from app.services import user_service
from app.schemas import user

router = APIRouter()

@router.post("/users", response_model=user.UserResponse)
def create_user(data: user.UserCreate):
    # API層はロジックを持たず、サービスを呼ぶだけ
    return user_service.create_user(data)
```

### サービスの実装方法 (`services/`)
```python
from app.crud import user_crud

def create_user(data):
    # 複雑な計算や外部APIの呼び出しはここで行う
    user = user_crud.create(data)
    # 必要に応じて他のサービスを呼び出し
    # notification_service.send_welcome_mail(user.email)
    return user
```

---

## Report API

`GET /api/v1/companies/{company_id}/report/monthly` は前月分の月次レポートを返します。

処理順序:

1. `tenants/{company_id}/reports/monthly/{YYYY-MM}/report.json` を Cloud Storage から確認します。
2. `APP_ENV=local`、`DRY_RUN=true`、または `WIKI_BUCKET` 未設定の場合は `.local_storage/` 配下の local storage emulator を確認します。
3. 保存済み JSON が存在する場合はそれを正本として返します。
4. 存在しない場合は BigQuery の `knowledge_nodes` / `survey_responses` から前月分を集計し、同じ path に JSON として保存します。
5. BigQuery データがない DRY_RUN 環境では `app/storage_seed/companies/*/structured_knowledge.json` からデモ用の月次レポートを生成します。

返却データは `header`、`monthly`、`metrics`、`charts`、`sections`、`highlights`、
`snippets`、`recommendation` を含み、フロントエンドの `/report` 画面でそのまま表示されます。

---

## 開発環境のセットアップ

1.  **依存関係のインストール**
    ```bash
    # uv を使用しているため
    uv sync
    ```
2.  **テストの実行**
    ```bash
    pytest tests/
    ```

---

## BigQuery エミュレータの起動（ローカル実データ運用）

`DRY_RUN=true`（既定）では BigQuery への読み書きは行われず、全画面が
`app/storage_seed/` の seed サンプルにフォールバックします。intake 提出をグラフ・
ダッシュボードに実際に反映させたい場合は、以下の手順でエミュレータ運用に切り替えます。

### 手順

1. `back/.env` を編集する:
   ```dotenv
   DRY_RUN=false
   # WIKI_BUCKET は必ず空（または未設定）にする。ダミー値のままだと
   # 原文保存が実 GCS に向かい 404 → intake 提出が 500 になる。
   #WIKI_BUCKET=""
   BIGQUERY_EMULATOR_HOST=http://bigquery-emulator:9050
   PROJECT_ID=local-project   # エミュレータ起動時の --project と一致必須
   ```
2. スタックを起動する（`docker compose up` は env_file を再読込して作り直すため、
   `.env` 変更後も `make dev` でよい。`docker compose restart` は env を再読込しないので不可）:
   ```bash
   make dev
   ```
3. **seed を投入する（エミュレータ起動のたびに必要）**:
   ```bash
   make seed-emulator
   ```

### 注意点

- **エミュレータは永続化ボリュームを持たない**ため、コンテナが再起動するとデータは
  すべて消えます。`make dev` を Ctrl+C で止めて上げ直した場合は `make seed-emulator`
  を再実行してください（動かしたまま裏で `make dev` した場合は不要）。
- データセットは全社共有の1つ（`BQ_DATASET_PREFIX`、既定 `consultant_copilot`）で、
  企業ごとの区別はテーブル名プレフィックス（例 `SMB_1042_knowledge_nodes`）で行います。
- 実 GCP には接続しません（`APP_ENV=local` ＋ `BIGQUERY_EMULATOR_HOST` 設定時は
  匿名認証でエミュレータへ、Cloud Storage は `WIKI_BUCKET` が空なら `.local_storage/` へ）。

### 動作確認

- `GET /api/v1/health` → `"dry_run": false` になっているか
- `GET /api/v1/companies/SMB-1042/graph/slice` → `meta.source` が `"bigquery"` か
  （`"sample"` なら seed 未投入 or エミュレータ未起動でフォールバック中）
- グラフ画面（/graph）の subtitle が「BigQuery 実データ」表示になっているか

詳細な設計背景は `docs/spec/continuous_discovery_agent_design.md` §23.2 / §23.4 を参照。
