# Continuous Discovery Agent - Google Cloud / Agent SDK 検討パッケージ

このzipは、これまでの壁打ち内容をもとに、Google Cloud上でAgent SDK / ADKを用いて構築する前提の検討資料・設計メモ・プロンプト/コンテキスト・BigQuery DDL・Cloud Storage階層案・マイグレーション方針・簡易実装スケルトンをまとめたものです。

## 想定プロダクト

Continuous Discovery Agentは、中小企業やコンサルタント向けに、初期ヒアリング・追加質問・現場観測を通じて、企業固有のKPI、重点管理指標、観測シグナル、LLM Wikiを形成するAI組織学習支援プラットフォームです。

## 主要コンポーネント

- Orchestrator Agent: 全体進行、承認、Knowledge/Research Agentの制御
- Knowledge Agent: 回答分析、KPI/重点管理指標設計、Wiki作成、BigQuery書き込み計画
- Research Agent: Knowledge Agentのresearch_planに基づく追加質問・観測情報収集
- BigQuery: 共通マスタ、企業別データセット、候補/現在定義/回答ログ
- Cloud Storage: Rawデータ、LLM Wiki、derived canonical JSON、バージョン管理

## ディレクトリ

```text
continuous_discovery_agent_bundle/
  docs/                         # 設計資料
  agents/                       # 各Agentのコンテキスト/プロンプト
  bigquery/                     # DDL / マイグレーション案
  cloud_storage/                # Cloud Storage階層と運用ルール
  wiki_templates/               # LLM Wikiのテンプレート
  src/                          # ADK実装イメージ/ツールI/Fの雛形
  examples/                     # 入出力JSON例
```

## 注意

このパッケージは設計・実装検討用のドラフトです。実装時には、実際のGoogle Cloudプロジェクト、IAM、データリージョン、社内セキュリティ要件に合わせて調整してください。
