# agents/

`agent/`サービスが提供する各AIエージェントの実装を置くディレクトリです。1ファイル = 1エージェント = 1責務とし、対応する`prompts/*.md`(プロンプト)、`tools/`(外部I/O)、ルートの`skills/`定義と1対1で対応させます。

## 各エージェントの役割

| ファイル | 役割 | 対応するプロンプト | 対応するスキル |
|---|---|---|---|
| `knowledge_agent.py` | **（実装済み）** 非構造テキストから観察事実・仮説・エンティティ・関係を抽出（Continuous Discovery 本体） | `prompts/knowledge_extraction.md` | （Continuous Discovery 用・QualityOps外） |
| `quality_eval_agent.py` | PR diff + Playwright証跡から品質スコア・リスクレベルを評価 | `prompts/quality_eval.md` | `quality-evaluation` |
| `cost_guard_agent.py` | AI呼び出し・Cloud Runのコストを見積もり、予算超過を検知 | (未作成) | `cost-guard` |
| `release_gate_agent.py` | 評価結果から `allow` / `block` / `needs_approval` を提案 | `prompts/release_gate.md` | `release-gate` |
| `report_agent.py` | 各エージェントの結果を統合し、PRコメント用レポートを生成 | `prompts/report.md` | `pr-report` |
| `test_data_agent.py` | FastAPIエンドポイント用のテストデータを生成 | `prompts/test_data.md` | `fastapi-testdata` |
| `ui_review_agent.py` | Playwrightのスクリーンショット/トレースをレビュー | `prompts/ui_review.md` | `playwright-ui-review` |

## 現在の実装状態

- `knowledge_agent.py`: **実装済み**。Gemini 構造化出力（mock フォールバック付き）で抽出を行い、FastAPI 経由で `back/` に提供します（下記「知識抽出サービス」参照）。
- QualityOps 系（`quality_eval` / `cost_guard` / `release_gate` / `report` / `test_data` / `ui_review`）: 固定値を返すプレースホルダ（MVPスケルトン）。

```python
def propose_release_gate() -> dict[str, str]:
    return {"decision": "conditional_go", "reason": "placeholder"}
```

---

## 知識抽出サービス（FastAPI）

`agent/` を Cloud Run 上の独立サービスとして FastAPI 化し、知識抽出を HTTP API で
提供します（`DESIGN.md` の Agent セクション）。

### エンドポイント（[app/main.py](app/main.py)、ポート 8080）

| メソッド | パス | 役割 |
|---|---|---|
| GET | `/healthz` | ヘルスチェック |
| POST | `/v1/knowledge/extract` | 非構造テキストから知識を抽出 |

**入力**（`ExtractionRequest`）: `source_type` / `body` / `workspace`（企業コンテキスト）。
**出力**（`ExtractionResult`）: `observations` / `hypotheses` / `entities` / `relationships` /
`extraction_method`。観察事実（fact）と仮説（hypothesis）は別リストに分離します（Requirement 6）。

- `entities[].entity_type`: `CustomerSegment` / `Product` / `Issue` / `Competitor` /
  `CompetitiveEvent` / `KPI`
- `relationships[].relationship_type`: `MENTIONS` / `HAS_ISSUE` / `RELATES_TO` /
  `COMPETES_WITH` / `MAY_CAUSE` / `IMPACTS` / `SUPPORTS` / `CONTRADICTS`

### mock / Gemini の切り替え

[agents/knowledge_agent.py](agents/knowledge_agent.py) の `extract_knowledge()` が本体です。

- `settings.use_gemini`（= `MOCK_MODE=false` かつ `GEMINI_API_KEY` あり）のときのみ Gemini を呼び、
  それ以外は決定論的なキーワードベースの mock を返します。
- Gemini 呼び出しは `google-genai` の構造化出力（`response_schema`）。`from google import genai` は
  `_gemini_extract` 内で遅延 import するため、mock 動作やテストでは SDK もキーも不要です。
- 解釈不能な応答は mock にフォールバックします。

### ディレクトリ構成（追加分）

```text
app/   FastAPI ランタイム（config / schemas / main）
```

### 環境変数（agent/.env）

```text
APP_ENV=local
MOCK_MODE=true
GCP_PROJECT=local-project
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
```

### ローカル実行

```bash
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8080
uv run pytest
```

Docker Compose 経由はリポジトリルートで `make dev`（または `docker compose up agent`）。
Dockerfile の CMD は `uvicorn app.main:app`（常駐サーバ）です。

### back からの利用

`back/` は [agent_client.py](../back/app/services/agent_client.py) の `extract_knowledge()` から
`POST {AGENT_BASE_URL}/v1/knowledge/extract` を呼びます。agent 未起動・到達不可、または back 側が
`MOCK_MODE=true` の場合は back 内のローカル抽出にフォールバックするため、agent が落ちていても
back は停止しません。結果は back の `Observation` / `Hypothesis` に変換され、entities / relationships は
back に保存されます（グラフ描画への接続は tasks.md セクション12として後続）。

### tasks.md 進捗（セクション7）

| タスク | 状態 |
|---|---|
| 7.1 構造化抽出スキーマ定義 | 完了 |
| 7.2 抽出プロンプトビルダー | 完了 |
| 7.3 Knowledge Agent 抽出ワーカー | 部分（raw 出力のデバッグ保存が未） |
| 7.4 エンティティ正規化 | 部分（抽出内 dedup のみ。type/正規化照合・entity_id 付与は未） |
| 7.5 リレーションシップ生成 | 部分（抽出のみ。BigQuery 行・entity_id・first/last_seen は未） |
| 7.6 仮説生成 | 部分（分離・supporting は実装。contradicting・status 遷移は未） |
| 7.7 エビデンス保持 | 部分（quote 保持は実装。永続化・検索連携は後続） |

## 出力契約

[AGENTS.md](../../AGENTS.md)のルールにより、ダウンストリームの意思決定に使う出力はすべて`skills/quality-evaluation/output-schema.json`に準拠したスキーマ検証を通す必要があります。各エージェント関数の返り値を素のdictのまま`back/`に渡さず、Pydanticモデル(`quality_eval_agent.py`の`QualityEvaluationResult`が一例)で構造化してください。

## テスト

対応するテストは`agent/tests/`に置きます。スコアリングロジックなど共通処理は`eval/`に切り出し、エージェント本体は薄く保ちます(`eval/scoring.py`の`clamp_score`が例)。