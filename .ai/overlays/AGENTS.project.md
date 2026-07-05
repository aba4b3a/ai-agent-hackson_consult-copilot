# Project Agent Overlay（プロジェクト用エージェント上書き）

`.ai-common/standards/AGENTS.base.md` の **後ろに** 適用されます。ベースを **厳しくすることはできますが、緩めることはできません**。

## プロジェクトコンテキスト

- プロダクト名: Consult Copilot（`front/app/layout.tsx` のメタデータ: "AI organization learning platform for consultants"）。
- 主要なユーザ向け画面: `/`（Discovery Feed）, `/intake`, `/research`, `/knowledge`, `/graph`（Knowledge Graph）, `/wiki`, `/approvals`, `/report`（Report Copilot）, `/report-chat`。詳細は `DESIGN.project.md` の「重要画面」を参照。
- 重要ワークフロー（Release Gate が「絶対にデグレさせない」対象）:
  - Intake（`/intake` サーベイ回答）→ Research（`/research` 追加質問アサインメント）→ Knowledge 抽出（`agent/agents/agent.py` の `root_agent`/`research_agent`/`knowledge_agent` が BigQuery ノード/エッジ・Wiki・KPI 候補を生成）→ `/graph` `/wiki` `/knowledge` での可視化 → `/approvals` での人間承認。
  - `back/app/services/copilot_service.py` ⇔ `agent/`（ADK API サーバー、ポート 8080）間のセッション疎通（Persistent AI Chat・Report Copilot の裏側）。
  - 左サイドメニュー（`BottomNav.tsx`、`md:` 幅で固定左カラム化）からの各画面遷移が 404 にならないこと（Firebase Hosting の `trailingSlash` 設定と `next export` の出力形式の整合性に依存。過去に不整合で全画面 404 の実績あり）。
  - オンコール / 承認者ロール: 未定義（TBD）。チームで決めたら本セクションを更新すること。

## このプロジェクト固有の厳格ルール

- `agent/agents/agent.py` の `root_agent` は本番で実際に配信される Continuous Discovery Agent 本体である。同ディレクトリの `cost_guard_agent.py` / `quality_eval_agent.py` / `release_gate_agent.py` / `report_agent.py` / `test_data_agent.py` / `ui_review_agent.py` は **未配線のプレースホルダ**（ハードコード値を返すのみ、どこからも import されない）であり、本実装と混同して削除・上書きしないこと。QualityOps スキルの実装先として使う場合は、まずこれらが本当にプレースホルダのままかを確認すること。
- `front/` の画面間ナビゲーションはすべて `components/feature/discovery/BottomNav.tsx` の `<a href>` に一本化されている。新しい画面を追加する場合は、この一覧と Firebase Hosting の静的ファイルレイアウト（`out/<route>.html`、`out/<route>/index.html` ではない）の両方を更新すること。

## ベースからの逸脱（要承認）

- BigQuery: ベース `DESIGN.md` は「オプトイン、既定は利用しない」としているが、本プロジェクトは `back/app/services/dashboard_service.py` / `research_service.py` が企業ごとの BigQuery データセットへ直接読み書きする **必須の中核コンポーネント**として使っている。Cost Guard はこれを前提に予算試算すること。
- `infra/terraform/environments/dev` は Artifact Registry 以外のモジュール（cloud_run, firestore, bigquery, iam, secret_manager, storage, budget, research_dispatch）を **まだ呼び出していない**。Terraform 上は宣言されているだけで dev 環境には未適用の状態。
