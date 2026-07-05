# Project Claude Overlay（プロジェクト用 Claude Code 上書き）

`.ai-common/standards/CLAUDE.base.md` の **後ろに** 適用されます。Claude Code 固有のプロジェクト入口情報をまとめます。

## クイックスタート

- Claude が主に触るディレクトリ: `front/`（Next.js UI, App Router）, `back/app/`（FastAPI, `api/v1/endpoints` + `services/`）, `agent/agents/`（ADK エージェント。`agent.py` が本番、他の `*_agent.py` はプレースホルダ）, `infra/`（Terraform / Firebase / Cloud Build）。
- ローカル開発コマンド: ルートで `make dev`（`docker compose up --build`、front:3000 / back:8000 / agent:8080 / BigQuery emulator / Ollama をまとめて起動）。個別には `front`: `npm run dev`、`back`: `uvicorn app.main:app --reload --port 8000`、`agent`: `adk api_server --host 0.0.0.0 --port 8080 /app/agents`。
- ローカルテストコマンド: `back`: `pytest`（`back/pyproject.toml` の `[tool.pytest.ini_options]`）。`agent`: `pytest`（`agent/tests/`）。`front`: Playwright テストは `front/tests/e2e/` に存在し `playwright.config.ts` で設定済みだが、**`make test` / `Makefile` が呼ぶ `npm run test:e2e` は `front/package.json` に未定義**（現状 `npm error Missing script`）。動かす場合は `npx playwright test` を直接使うこと。
- ローカル型チェックコマンド: `agent`: `mypy .`（`mypy` は `agent/pyproject.toml` の dev 依存に含まれる）。`front`: `npx tsc --noEmit -p tsconfig.json`。`back`: **`make lint` が呼ぶ `mypy app` は現状動かない**（`back/pyproject.toml` の dev 依存に `mypy` が無く、`back/.venv` にも入っていない）。型チェックしたい場合は先に `mypy` を dev 依存へ追加する必要がある。同様に `make lint`/`make test` が呼ぶ `front` 側の `npm run typecheck` / `npm run test:e2e` も `front/package.json` に未定義で失敗する（`npm run lint` は next lint のみ、型チェックは含まない）。Playwright テスト自体は `front/tests/e2e/` にあるので `npx playwright test` で直接実行できる。

## プロジェクト固有スキル

- [`project-quality-rubric`](skills/project-quality-rubric/SKILL.md): `/graph` のホバー全文表示・フィルタ動作、左サイドメニュー遷移の 404 防止、front↔back のエンドポイント整合性など、この実装固有の受け入れ基準。

## プロジェクト固有 MCP メモ

- 現時点でベース（`filesystem`, `playwright`）以外の MCP サーバーは有効化していない。
- Playwright で `front` を検証する場合、静的書き出し (`next build && next start` 相当がないため) は `npm run dev`（`http://127.0.0.1:3000`）を対象にする。本番同等の確認をしたい場合は `next build` 後の `out/` を静的サーバーで配信し、`infra/firebase/firebase.json` の `cleanUrls` / `trailingSlash` 設定と食い違うパス（`out/<route>.html` はあるが `out/<route>/index.html` は無い）に注意する。
