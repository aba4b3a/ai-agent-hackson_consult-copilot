# Gemini（Vertex AI）呼び出し設定メモ

2026-07-07 のトラブルシュートで確定した内容。agent（ADK）で実 Gemini を使うための設定と、ハマりどころの記録。

## 動作確認済みの構成（Vertex express・APIキー方式）

`agent/.env` に以下を設定する（キーの実値はコミットしない）:

```bash
MODEL_ID=gemini-3.1-flash-lite        # ← モデル選択はこの変数のみが有効
GOOGLE_GENAI_USE_VERTEXAI=true        # ← Vertex AI バックエンドに切替
GEMINI_API_KEY=AQ.xxxx...             # ← Vertex express キー（AQ. で始まる53文字）
```

- ADK の `Agent(model=settings.model_id)` → google-genai SDK が環境変数を読んで接続する。
- ローカルLLMに戻す場合は `MODEL_ID=ollama/gemma4:12b`（+ `OLLAMA_API_BASE`）。

## ハマりどころ（今回実際に踏んだもの）

1. **`LOCAL_MODEL_ID` / `PROD_MODEL_ID` / `GCP_PROJECT_ID` / `GCP_LOCATION` はコードに読まれていない。**
   `agents/config.py` が読むのは `MODEL_ID` / `PROJECT_ID`(または`GCP_PROJECT`) / `LOCATION` のみ。
   `.env.example` の記載と実装が乖離しているので注意（APP_ENV でのモデル自動切替も未実装）。

2. **APIキー方式では `GOOGLE_CLOUD_PROJECT` / `GOOGLE_CLOUD_LOCATION` を設定しないこと。**
   google-genai SDK は「project/location が環境変数にあると APIキーを破棄して ADC 認証に切替える」
   優先ルールを持つ。設定すると 401 UNAUTHENTICATED になる。location は自動で global になる。

3. **`GOOGLE_API_KEY` はどこにも設定しないこと。**
   SDK は `GOOGLE_API_KEY` > `GEMINI_API_KEY` の優先で読む。両方あると GOOGLE_API_KEY が勝つ。

4. **キー貼り付け時の `=` 二重化に注意。**
   `GEMINI_API_KEY==AQ....` になっていて全モード認証失敗した（値の先頭に `=` が混入）。
   症状: Vertex では 401「API keys are not supported」、Developer API では 400「API key not valid」。
   → キーが疑わしいときは長さ(53)と接頭辞(`AQ.`)を確認する。

5. **`.env` を変更したらコンテナの「再作成」が必要。**
   `docker compose restart` では env_file が再読込されない。
   ```bash
   docker compose up -d --force-recreate agent back
   ```

6. **back → agent の接続は `AGENT_BASE_URL=http://agent:8080`（back/.env）。**
   `localhost:8080` はコンテナ自身を指すため不通 → back はサンプル応答にフォールバックする。

## 「AIが動いているか」の確認方法

back の copilot はエラー時に **サンプルデータへ静かにフォールバックする**
（`back/app/services/sample_company_data.py`。応答に「サンプルデータに基づく回答です」と出る）。
応答が返る＝AI が動いた、ではない点に注意。

確認手順:

```bash
# 1) agent 単体で Gemini 疎通（コンテナ内から）
docker compose exec agent python -c "from google import genai; print(genai.Client().models.generate_content(model='gemini-3.1-flash-lite', contents='1+1は?').text)"

# 2) 本番経路（copilot）
curl -X POST http://localhost:8000/api/v1/companies/SMB-1042/report/copilot \
  -H "Content-Type: application/json" -d '{"message":"KPI候補を1つ挙げて"}'
# → 応答に「サンプルデータに基づく回答です」が含まれないこと

# 3) agent ログに以下が出ること
docker compose logs agent --tail 20
#   "Response received from the model" / "POST /run" 200
```

## 関連: BigQuery エミュレータ（agent 側）

agent の BQ ツール群（insert_kpi_candidates 等）をローカルで使う場合は `agent/.env` に:

```bash
BIGQUERY_EMULATOR_HOST=http://bigquery-emulator:9050
PROJECT_ID=local-project   # compose のエミュレータ起動プロジェクト名と一致させる
```
