# Architecture

## Agent構成

```text
Orchestrator Agent
  ├─ Knowledge Agent
  └─ Research Agent
```

## Agent責務

### Orchestrator Agent

- 初期オンボーディング開始
- Knowledge Agent / Research Agentの実行制御
- 人間承認が必要な項目の検出
- 承認済み成果物のPublish制御

### Knowledge Agent

- 初期回答・追加回答の分析
- 企業プロファイル作成
- KPI候補・重点管理指標候補作成
- Research Plan作成
- LLM Wiki作成/更新
- BigQueryへの候補/定義/ログ書き込み計画作成

### Research Agent

- Knowledge Agentのresearch_planに基づく情報収集
- 対象者・頻度・質問文の具体化
- 回答に応じた追加質問
- 回答結果の構造化
- Knowledge Agentへの観測データ返却

## Data構成

```text
Cloud Storage
  raw/      原回答、添付、外部情報
  wiki/     LLM Wiki、KPI定義、重点管理指標、調査方針
  derived/  canonical JSON/YAML、BQ投入前成果物

BigQuery
  cd_common         共通マスタ
  cd_tenant_x       企業別データセット
```

## 基本フロー

1. Orchestratorが初期18問の回答を受け取る
2. Raw回答をCloud Storageに保存
3. 要約/抽出結果をBigQueryに保存
4. Knowledge AgentがKPI候補・重点管理指標候補・Wiki案・Research Planを作成
5. 候補をBigQueryに保存、Wiki案をCloud Storageに保存
6. Research AgentがResearch Planに基づき追加質問
7. 追加回答を保存
8. Knowledge Agentが候補・Wiki・Research Planを更新
9. Orchestratorが人間承認後、current定義へ反映
