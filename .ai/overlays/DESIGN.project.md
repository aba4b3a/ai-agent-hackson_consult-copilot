# Project Design Overlay（プロジェクト用設計上書き）

`.ai-common/standards/DESIGN.base.md` の **後ろに** 適用されます。プロジェクト固有のアーキテクチャ詳細を追加するもので、ベースの方針に **矛盾しない** 範囲で書きます。

## コンポーネント

- `front/`: Next.js 16 (App Router, Turbopack) + TypeScript。`output: "export"` で静的書き出しし Firebase Hosting へデプロイ（`infra/firebase/firebase.json`）。画面は `PhoneFrame` でモバイル UI をモックしたコンサルタント向け業務画面群。ナビゲーションは `components/feature/discovery/BottomNav.tsx` 一本で、モバイル幅ではボトムタブ、`md:` 以上では固定の左サイドメニューに切り替わる（`fixed md:inset-y-0 md:left-0 md:w-32`）。認証・会社切り替えは `AppShell` / `AuthProvider` / `CompanySwitcher`。データ取得は React Query の `hooks/use-*.ts` → `services/*-service.ts` → `NEXT_PUBLIC_API_BASE_URL` 経由で `back/` の REST API。
- `back/`: FastAPI（`app_name = "Continuous Discovery Agent API"`）。ルーターは `app/api/v1/router.py` に集約され、`/api/v1/companies/{company_id}/...` 配下に health / companies / bigquery / survey / graph・graph_nodes / custom_tables / wiki / dashboard / knowledge_stats / report / copilot / approvals / research / observation_signals、加えて `/migrations`, `/schema-validation` がある。永続化は Firestore（アサインメント・セッション状態）と BigQuery（企業ごとのデータセット `{BQ_DATASET_PREFIX}_{company_id}`、`knowledge_nodes` / `knowledge_edges` / `followup_answer_events` 等）、Cloud Storage（Wiki バケット）。`copilot_service.py` はユーザーのチャットメッセージを HTTP 経由で `agent/` の ADK API サーバーへプロキシする（`AGENT_BASE_URL`、既定 `http://localhost:8080`）。
- `agent/`: 1つの Cloud Run サービス配下に **性質の異なる 2 種類のエージェント** が同居している。
  1. **プロダクト本体（Continuous Discovery Agent）**: `agent/agents/agent.py` の `root_agent`（= orchestrator_agent、`research_agent` / `knowledge_agent` を sub_agents に持つ）。BigQuery DDL 生成・Firestore/Storage 書き込み・Wiki レンダリングなど実ツール（`tools/bigquery_tools.py` 等）を持つ、実際にユーザーの調査・ナレッジ抽出を行う本番ロジック。Dockerfile の `CMD ["adk", "api_server", ..., "/app/agents"]` で ADK API サーバーとして起動し、`back` の `copilot_service` はこのプロセスと会話する。
  2. **QualityOps 用プレースホルダ群**: `agent/agents/cost_guard_agent.py`, `quality_eval_agent.py`, `release_gate_agent.py`, `report_agent.py`, `test_data_agent.py`, `ui_review_agent.py`。`.ai-common` のスキル名（cost-guard / quality-evaluation / release-gate / pr-report / fastapi-testdata / playwright-ui-review）に対応する想定だが、現状は **ハードコードされた固定値を返すだけの MVP プレースホルダ**で、どこからも import されておらず ADK アプリにも登録されていない（`root_agent` のみが実際に配信される）。CI ワークフローからの呼び出しも未配線。これらのファイルを本実装だと誤認しないこと。
- `infra/`: Terraform モジュールは `infra/terraform/modules/` に artifact_registry / bigquery / budget / cloud_run / firestore / iam / research_dispatch / secret_manager / storage が用意されているが、`environments/dev/main.tf` は現状 `locals` のみで、実際にリソースとして呼び出されているのは Artifact Registry だけ（`outputs.tf` が参照）。他モジュールは未接続。デプロイは `infra/cloudbuild/cloudbuild.yaml` が `front` のビルド（`npm run build` → `out/`）、`back` と `agent` の Docker イメージビルド・push・Cloud Run デプロイ（`--no-allow-unauthenticated`, `min-instances=0`）を行うが、**Firebase Hosting へのデプロイ手順はこのパイプラインに含まれていない**（`firebase deploy` を別途手動実行する前提）。

## 外部連携

- Gemini API（`MODEL_ID`、既定 `gemini-3.1-pro` / ローカルは `agent/.env` で Ollama 経由の `ollama/gemma...` にフォールバック可）を ADK 経由で呼び出す。
- BigQuery: ベース設計 (`DESIGN.md`) では「オプトイン」扱いだが、本プロジェクトでは `back/app/services/dashboard_service.py` や `research_service.py` が直接クエリ・書き込みする **必須の中核永続化先**（企業ごとにデータセットを動的生成）。ベースからの明確な逸脱として扱うこと。
- Firebase Hosting（静的フロント配信）、Cloud Run（`back` / `agent`）、Cloud Storage（Wiki ファイル）。

## 重要画面

playwright-ui-review のスコープ限定に使う名前リスト（すべて `front/app/*/page.tsx`、ナビゲーションは `BottomNav`）:

- `/`（Home / Discovery Feed）
- `/intake`（初期サーベイ回答）
- `/research`（追加調査アサインメント）
- `/knowledge`（ナレッジ統計）
- `/graph`（Knowledge Graph マップ。ノード/クラスタラベルの truncate + hover 全文表示、フィルタタグと Graph Views ボタンでのノード絞り込みが機能要件）
- `/wiki`（企業 Wiki ファイル・バージョン一覧）
- `/approvals`（承認キュー）
- `/report`, `/report-copilot`（**同一コンポーネント `ReportCopilot` を描画する重複ルート**。ナビからは `/report` のみリンクされ、`/report-copilot` はブラウザ直打ちでのみ到達する未整理の重複——統合や削除を検討する余地あり）
- `/report-chat`（追加質問チャット。バックエンドに対応する `GET /report-chat` ルートが存在せず、`report-service.ts` の `try/catch` で常にハードコードのモック値にフォールバックする既知のギャップ）
- `/signin`

## ADR インデックス

- `docs/adr/` は未作成。ADR 運用はまだ開始していない。
