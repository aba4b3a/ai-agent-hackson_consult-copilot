---
name: project-quality-rubric
description: Project-specific acceptance criteria applied on top of the base quality-evaluation rubric. Use whenever quality-evaluation runs.
allowed-tools: Read Grep Bash
---

# Project Quality Rubric

Project-specific acceptance criteria. Composes with the base `quality-evaluation` skill.

## Inputs

- Base `quality-evaluation` output (schema-valid JSON).
- This project's critical-workflows list (see `DESIGN.project.md`).

## Procedure

1. Read base quality-evaluation result.
2. Apply project-specific stricter rules below.
3. Report any project rule that flips a base `pass` to `warn` or `block`.

## Project Rules

- `/graph`（Knowledge Graph）: truncate されたノードラベル・クラスタラベル・エッジラベルは `title` 属性でホバー時に全文が読めること。フィルタタグ（`全て`＋要素ごとのタグ）と Graph Views ボタンは押下でアクティブ状態が変わり、実際に表示ノードが絞り込まれること（見た目だけのボタンで終わっていないこと）。
- 左サイドメニュー（`front/components/feature/discovery/BottomNav.tsx`、`md:` 幅で固定左カラムになる）からのリンクは全画面で 404 にならないこと。`front/next.config.ts` の `output: "export"` は各ルートを `out/<route>.html` として書き出す（`out/<route>/index.html` にはならない）ため、`infra/firebase/firebase.json` の `trailingSlash` は必ず `false`（`cleanUrls: true` と組み合わせる）のままにすること。変更する場合は `next build` 後の `out/` の実ファイルレイアウトと突き合わせて確認する。
- `front/services/*-service.ts` の `apiFetch` が呼ぶ全パスは、`back/app/api/v1/router.py` に登録されたルーターの実際のパスと一致していること。`try/catch` でモックデータにフォールバックする実装（例: `report-service.ts` の `/report-chat`）は、対応するバックエンドルートが存在しないことを隠してしまうため、新規に同様のフォールバックを追加する場合は対応エンドポイントの有無を明示的に確認・報告すること。
- `agent/agents/agent.py` の `root_agent`（Continuous Discovery Agent 本体）を変更した場合は、`back/app/services/copilot_service.py` が期待する ADK セッション API（`app_name: "agents"`, `AGENT_BASE_URL`）との疎通を確認すること。`agent/agents/` 内の `cost_guard_agent.py` 等のプレースホルダ（未配線・固定値返却）を本実装だと誤認しないこと。

## Output

- Adjusted release-gate decision with explicit reasons.

## Guardrails

- No secrets or PII in evidence.
- Project rules may only tighten the base; they may not relax it.
