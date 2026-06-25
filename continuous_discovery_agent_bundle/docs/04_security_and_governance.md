# Security and Governance Notes

## 原則

- Agentに任意SQLを実行させない
- Agentごとにサービスアカウントを分ける
- Knowledge AgentのBigQuery権限は候補テーブルへのINSERT中心にする
- current_* テーブル更新は承認済み操作のみ許可する
- DROP/DELETE/ALTERはAgentツールから提供しない
- Rawデータは削除禁止、追記/バージョン管理を基本とする
- Cloud StorageのObject VersioningとLifecycle Managementを有効化する

## サービスアカウント例

- orchestrator-sa: ワークフロー制御、承認状態参照
- knowledge-agent-sa: candidate insert、wiki write、approved current upsert
- research-agent-sa: followup question insert、answer raw write
- migration-sa: DDL適用専用。通常Agentからは使わない

## Human-in-the-loop

人間承認が必要なもの:

- KPIの本番採用/廃止
- 重点管理指標の本番採用/廃止
- BigQueryスキーマ変更
- source_refsが弱いWiki更新
- confidence < 0.7 の情報に基づく定義更新
