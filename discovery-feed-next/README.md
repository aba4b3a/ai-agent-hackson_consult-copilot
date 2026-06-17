# Discovery Feed / Knowledge Formation UI

Next.js App Router + React + Tailwind CSS + TanStack Query で構成した、スマホ・PC両対応のサンプル画面です。

## 画面

- `/` : Discovery Feed
- `/knowledge` : Knowledge Formation

スマホ幅では添付画像に近い縦長の画面と下部タブを表示します。`md` 以上のPC表示では下部タブを非表示にし、中央にスマホフレーム風のカードとして表示します。

## Frontend Architecture

本プロジェクトは、Next.js App Router を使用したWebアプリケーションです。
保守性、テスト容易性、およびデータ取得の効率化を目的として、以下のアーキテクチャとライブラリを採用しています。

- Static Export 対応: Firebase Hosting 等に載せやすい構成
- TanStack Query: API/データ取得のキャッシュ管理・状態管理
- レイヤードアーキテクチャ: 責務を分離したクリーンなディレクトリ構成

## フォルダ構成と役割

```txt
app/                  # ルーティング、ページUI、レイアウト、プロバイダー設定
components/
  feature/            # 特定の業務機能を持つUIコンポーネント
  ui/                 # 再利用可能な汎用UIパーツ
hooks/                # TanStack Query等を使用したデータ取得・状態操作
lib/                  # ライブラリ設定、型定義
services/             # 外部API通信、データ操作、モックデータ
utils/                # 汎用的な純粋関数
```

## データの流れ

```txt
Components -> Hooks -> Services -> Lib/API
```

- Components: UI表示に専念。直接サービス層を呼ばず、`hooks/` を経由します。
- Hooks: `useQuery` 等を使用して、データ取得状態を管理しUIに提供します。
- Services: データ取得・加工などの業務ロジックを保持します。
- Lib: 型定義やQueryClient設定など、共通設定を保持します。

## 実装メモ

- `app/api` は使用していません。
- 実API化する場合も `services/*-service.ts` からクライアントサイドで外部APIを呼び出す想定です。
- APIレスポンス型は `lib/schemas.ts` に集約しています。
- 複雑な画面UIは `components/feature/` に配置しています。
- 小さな共通UIは `components/ui/` に配置しています。

## コマンド

```bash
npm install
npm run dev
npm run build
```

## 追加画面

- `/graph`: Knowledge Graph 画面
  - スマホ幅では下部メニューを表示し、Graph タブをアクティブ化します。
  - `md` 以上のPC幅では下部メニューを非表示にし、中央のスマホフレームとして表示します。
  - データ取得は `components -> hooks -> services -> lib` の依存方向に沿って `useGraph` / `getGraphData` / `GraphData` で分離しています。


## 実装済み画面

- `/` Discovery Feed
- `/knowledge` Knowledge Formation
- `/graph` Knowledge Graph
- `/report` Report Copilot
- `/report-chat` Report Chat

スマホ表示では下部タブを表示し、`md` 以上のPC表示では下部タブを非表示にします。
