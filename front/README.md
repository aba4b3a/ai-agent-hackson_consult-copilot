# Frontend Architecture

## 概要
本プロジェクトは、Next.js 16 (App Router) を使用したWebアプリケーションです。
保守性、テスト容易性、およびデータ取得の効率化を目的として、以下のアーキテクチャとライブラリを採用しています。

- **Static Export (SSG)**: Firebase Hosting に対応した構成
- **TanStack Query**: API/データ取得のキャッシュ管理・状態管理
- **レイヤードアーキテクチャ**: 責務を分離したクリーンなディレクトリ構成

## フォルダ構成と役割

```text
├── app/          # ルーティング、ページUI、レイアウト、プロバイダー設定
├── components/   # UIパーツ
│   ├── feature/  # 特定の業務機能を持つUIコンポーネント
│   └── ui/       # 再利用可能な汎用UIパーツ (Button, Input等)
├── hooks/        # カスタムフック: TanStack Query等を使用したデータ取得・状態操作
├── lib/          # ライブラリ設定: APIクライアント、TanStack Query設定、型定義
├── services/     # ビジネスロジック: 外部API通信、Firebase SDK等のデータ操作
├── utils/        # ユーティリティ: 汎用的な純粋関数 (日付変換、計算等)
└── tests/        # テストコード (e2e 等)
```

---

## アーキテクチャ・ルール

### 1. データの流れ (依存関係)
レイヤーの逆流を防ぐため、以下の方向を守ってください。
> **Components** → **Hooks** → **Services** → **Lib/API**

- **Components**: UI表示に専念。直接サービス層を呼ばず、`hooks/` を経由する。
- **Hooks**: `useQuery` 等を使用して、データ取得状態を管理。UIに提供。
- **Services**: データ取得・加工などの業務ロジック。UIやHooksの存在を知らない。
- **Lib**: 設定や共通の型定義。プロジェクト全体で利用可能。

### 2. TanStack Query の利用
すべてのデータ取得は `TanStack Query` を通して行います。
- `lib/react-query.ts` で初期設定を行っています。
- `app/layout.tsx` の `QueryClientProvider` により、アプリ全体でキャッシュが共有されます。

---

## 実装ガイドライン

### サービス層 (`services/`)
```typescript
// services/user-service.ts
import { apiClient } from "@/lib/api-client";

export const getDashboardData = async () => {
  const { data } = await apiClient.get("/dashboard");
  return data;
};
```

### フック層 (`hooks/`)
```typescript
// hooks/use-dashboard.ts
import { useQuery } from "@tanstack/react-query";
import { getDashboardData } from "@/services/user-service";

export const useDashboard = () => {
  return useQuery({
    queryKey: ['dashboard'],
    queryFn: getDashboardData,
  });
};
```

### UIコンポーネント (`components/`)
```tsx
// components/feature/Dashboard.tsx
"use client";
import { useDashboard } from "@/hooks/use-dashboard";

export const Dashboard = () => {
  const { data, isLoading } = useDashboard();
  if (isLoading) return <div>Loading...</div>;
  return <div>{data.summary}</div>;
};
```

---

## 開発・運用ルール

1.  **Static Export の制約**: API Routes (`app/api`) は使用不可です。外部API通信は必ずクライアントサイド（サービス層）から行ってください。
2.  **型安全**: `lib/schemas.ts` に API のリクエスト/レスポンス型を一元管理してください。
3.  **コンポーネントの分割**: 
    - 複雑なロジックを持つUIは `components/feature/` へ。
    - デザインのみに依存する小さなパーツは `components/ui/` へ。

---

## Report 画面

`app/report/page.tsx` は `components/feature/report-copilot/ReportCopilot.tsx` を表示します。
この画面は Report Copilot のチャットだけでなく、前月分の Monthly Discovery Report を
報告書として読むためのビューです。

データ取得の流れ:

```text
ReportCopilot.tsx
  -> hooks/use-report-copilot.ts
  -> services/report-copilot-service.ts
  -> GET /api/v1/companies/{company_id}/report/monthly
```

表示する主な要素:

- Cloud Storage から読み込んだか、未存在のため生成したかの status
- レポート期間と保存 path
- Executive summary
- 事実、仮説、根拠件数、平均 confidence のメトリクス
- 月次指標の棒グラフ
- 事実と仮説を分けたハイライト
- Evidence snippets
- Report Copilot への質問欄

`ReportCopilotData` の型は `lib/schemas.ts` に集約されています。API レスポンスを変更する場合は、
先にこの型と画面表示の両方を更新してください。

---

## コマンド
- 開発サーバー: `npm run dev`
- ビルド (Static): `npm run build`
- テスト実行: `npx playwright test`
