# フロントエンド設計

`front/` は Consult Copilot の画面実装です。Next.js 16.2.9、React 19.2.7、TypeScript を使い、MVP では Static Export を前提にします。

## 概要

- UI は `components/feature/*` に機能単位で配置します。
- API 呼び出しは `services/` に集約します。
- TanStack Query の hook は `hooks/` に置きます。
- バックエンドの接続先は `NEXT_PUBLIC_API_BASE_URL` で切り替えます。

## フォルダ構成

```text
app/          App Router のページ
components/   共通 UI と feature UI
hooks/        TanStack Query hooks
lib/          API client などの共通処理
services/     backend API 呼び出し
```

## アーキテクチャ・ルール

### データの流れ

```text
page / component -> hook -> service -> lib/api-client -> backend API
```

UI から直接 `fetch` せず、service 層に寄せます。

### TanStack Query

- query key は feature ごとに一貫した名前にします。
- mutation 後は関連 query を invalidate します。
- loading / error / empty state を画面側で明示します。

## 実装ガイドライン

### services/

- endpoint path と response 型をここに集約します。
- `api-client.ts` を通して `NEXT_PUBLIC_API_BASE_URL` を使います。
- 画面都合の整形は services ではなく hook または component 側に寄せます。

### hooks/

- API 呼び出しの cache、retry、enabled 条件を管理します。
- component は hook の戻り値を表示に使うだけにします。

### components/

- feature ごとに責務を分けます。
- 画面間 navigation は `components/feature/discovery/BottomNav.tsx` に集約します。
- Static Export 前提のため、SSR 専用 API に依存しません。

## Report 画面

`/report` は `GET /api/v1/companies/{company_id}/report/monthly` を呼び、保存済みまたは生成済みの Monthly Discovery Report を表示します。事実、仮説、根拠、confidence、次月の推奨観測、Report Copilot への質問導線を扱います。

## コマンド

```bash
npm run lint
npm run typecheck
npm run build
```

Playwright の E2E テストは `front/tests/e2e/` にありますが、現状 `package.json` に `test:e2e` script はありません。必要な場合は `npx playwright test` を直接実行します。
