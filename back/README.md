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