# Continuous Discovery Agent: Elasticsearch活用版サービス構成

## 1. 位置づけ

このドキュメントは、**Continuous Discovery Agent** を Google Cloud 上で構築する前提で、検索・探索基盤として **Elasticsearch / Elastic Cloud on Google Cloud** を一部活用する場合のサービス構成を整理したものです。

Elasticsearchを入れることで、サービスは単なる「ナレッジ形成・可視化」から、**企業内外の非構造情報を高速に探索し、根拠を確認しながら組織学習を進めるプラットフォーム**に近づきます。

ただし、Elasticsearchはナレッジの正本DBではなく、主に以下の役割を担います。

- 商談メモ、日報、競合情報、求人、SNS、議事録などの高速全文検索
- 顧客名、商品名、競合名、エラーコード、条項番号などの厳密検索
- キーワード検索とベクトル検索を組み合わせたハイブリッド検索
- Strategy Copilot / Research Agent が根拠文書を探すための検索API
- コンサルタント向けの探索UI、ファセット検索、フィルタ検索
- 競合情報や観測ログの準リアルタイム検索

Elastic公式では、Elasticsearchは単一APIでBM25などの語彙検索とベクトル検索を組み合わせるハイブリッド検索を実現できると説明されています。また、Elastic CloudはGoogle Cloud Marketplace経由で利用でき、GCP請求と統合できます。

## 2. 全体サービス構成

```mermaid
flowchart TB

%% =====================
%% Input Layer
%% =====================
subgraph INPUT["入力チャネル"]
    A1["商談メモ"]
    A2["音声・会話ログ"]
    A3["日報・現場メモ"]
    A4["競合サイト / PR / 求人"]
    A5["SNS / 業界ニュース"]
    A6["KPI CSV / CRMデータ"]
end

%% =====================
%% Ingestion Layer
%% =====================
subgraph INGEST["収集・前処理層 on Google Cloud"]
    B1["Cloud Storage<br/>Raw Data Lake"]
    B2["Cloud Run Jobs<br/>Crawler / Batch Ingest"]
    B3["Pub/Sub / Eventarc<br/>イベント駆動"]
    B4["Document AI<br/>PDF・帳票抽出"]
    B5["Speech-to-Text<br/>音声文字起こし"]
    B6["Sensitive Data Protection<br/>PII検出・マスキング"]
end

A1 --> B1
A2 --> B5 --> B1
A3 --> B1
A4 --> B2 --> B1
A5 --> B2 --> B1
A6 --> B1
B1 --> B3
B3 --> B4
B3 --> B6

%% =====================
%% AI Processing
%% =====================
subgraph AI["生成AI・エージェント処理層"]
    C1["Vertex AI Gemini<br/>構造化抽出"]
    C2["Knowledge Curator Agent<br/>保存/破棄/重要度判定"]
    C3["Knowledge Formation Agent<br/>Entity / Relationship生成"]
    C4["Observation Agent<br/>重点観測項目更新"]
    C5["Discovery Agent<br/>変化検知・仮説生成"]
    C6["Strategy Copilot Agent<br/>壁打ち・説明生成"]
end

B6 --> C1
C1 --> C2
C2 --> C3
C3 --> C4
C4 --> C5
C5 --> C6

%% =====================
%% Search Layer
%% =====================
subgraph SEARCH["検索・探索層"]
    D1["Elasticsearch / Elastic Cloud on GCP<br/>全文検索・ファセット検索・ハイブリッド検索"]
    D2["Vertex AI Vector Search<br/>高精度ベクトル検索 / RAG"]
    D3["Vertex AI Search<br/>マネージドRAG / ドキュメント検索"]
end

B1 --> D1
C1 --> D1
B1 --> D2
B1 --> D3
C6 --> D1
C6 --> D2
C6 --> D3

%% =====================
%% Structured Knowledge
%% =====================
subgraph STRUCTURED["構造化ナレッジ層"]
    E1["BigQuery<br/>Observations / Entities / Relationships / KPI"]
    E2["BigQuery Graph<br/>分析用ナレッジグラフ"]
    E3["Spanner Graph<br/>低レイテンシ関係探索 ※本番拡張"]
    E4["Cloud Storage / Git Repo<br/>LLM Wiki"]
end

C2 --> E1
C3 --> E1
C3 --> E2
C3 --> E3
C3 --> E4
C4 --> E4
C5 --> E1

D1 --> C6
D2 --> C6
D3 --> C6
E1 --> C5
E2 --> C5
E4 --> C6

%% =====================
%% Visualization
%% =====================
subgraph UI["可視化・業務UI"]
    F1["Looker / Looker Studio<br/>KPI・変化検知ダッシュボード"]
    F2["Custom Web UI<br/>Knowledge Graph Viewer"]
    F3["Search Console<br/>全文検索・ファセット探索"]
    F4["Periodic Discovery Report<br/>週次/月次レポート"]
    F5["Strategy Copilot UI<br/>対話型分析"]
end

E1 --> F1
E2 --> F2
E3 --> F2
D1 --> F3
C5 --> F4
C6 --> F5
D1 --> F5
D2 --> F5
E4 --> F5
```

## 3. Elasticsearchを入れると変わる点

Elasticsearchを入れると、サービスは **「知識を形成する」だけでなく、「知識と原文を高速に探索する」** 方向に拡張されます。

### 変更前

```text
観測
↓
知識化
↓
発見
↓
仮説
↓
追加観測
↓
学習
```

### 変更後

```text
観測
↓
知識化
↓
検索可能化
↓
関係性可視化
↓
発見
↓
仮説
↓
追加観測
↓
学習
```

### 追加される価値

| 機能 | Elasticsearchありの場合の価値 |
|---|---|
| 原文検索 | 商談メモ、日報、競合情報を高速に検索できる |
| ファセット検索 | 顧客属性、商品、競合、期間、担当者で絞り込める |
| ハイブリッド検索 | キーワード一致と意味的類似を組み合わせられる |
| 根拠提示 | LLM回答の根拠発言を即座に提示しやすい |
| 競合監視 | 競合名、職種、技術、媒体、期間で探索できる |
| コンサルタントUI | 人間が仮説を立てながら検索できる |
| RAG | Geminiが回答生成前に関連原文を取得できる |

## 4. 検索ルーティング

ユーザーの問いに応じて、Elasticsearch、Vertex AI Vector Search、BigQuery Graph、BigQueryを使い分けます。

```mermaid
flowchart LR
    A["ユーザーの問い"] --> B{"検索タイプ判定"}

    B -->|"キーワード・固有名詞・正確な語句"| C["Elasticsearch<br/>全文検索"]
    B -->|"意味的に似た事例"| D["Elasticsearch Hybrid<br/>または Vertex AI Vector Search"]
    B -->|"関係性をたどる"| E["BigQuery Graph / Spanner Graph<br/>グラフ探索"]
    B -->|"KPI・時系列集計"| F["BigQuery<br/>分析SQL"]

    C --> G["候補文書・発言"]
    D --> G
    E --> H["関連エンティティ・関係"]
    F --> I["集計値・傾向"]

    G --> J["Gemini<br/>根拠付き回答"]
    H --> J
    I --> J
```

## 5. データ同期シーケンス

```mermaid
sequenceDiagram
    participant User as 入力者
    participant GCS as Cloud Storage
    participant PubSub as Pub/Sub / Eventarc
    participant PII as Sensitive Data Protection
    participant Gemini as Vertex AI Gemini
    participant ES as Elasticsearch
    participant BQ as BigQuery
    participant Graph as BigQuery Graph
    participant Wiki as LLM Wiki

    User->>GCS: 商談メモ・音声・日報を保存
    GCS->>PubSub: raw-data-created event
    PubSub->>PII: PII検出・マスキング
    PII->>Gemini: マスク済みテキスト
    Gemini->>Gemini: Observation / Entity / Relationship抽出
    Gemini->>ES: 原文・要約・タグ・embeddingをindex
    Gemini->>BQ: 構造化Observationを保存
    BQ->>Graph: Entity / Relationshipをグラフ化
    Gemini->>Wiki: 企業モデル・観測方針・仮説を更新
```

## 6. ElasticsearchのIndex設計

Elasticsearchには、原文検索用のIndexと、抽出済みナレッジ検索用のIndexを分けて持ちます。

```mermaid
erDiagram
    RAW_DOCUMENT {
        string tenant_id
        string document_id
        string source_type
        string source_uri
        datetime created_at
        string title
        string body
        string[] speakers
        string[] tags
        string[] products
        string[] competitors
        string[] customer_segments
        dense_vector embedding
    }

    OBSERVATION_DOC {
        string tenant_id
        string observation_id
        string source_document_id
        datetime observed_at
        string summary
        string raw_quote
        string issue_type
        string customer_segment
        string product
        string competitor
        float confidence
        dense_vector embedding
    }

    COMPETITIVE_EVENT {
        string tenant_id
        string event_id
        string competitor
        string event_type
        datetime event_date
        string summary
        string source_url
        string[] affected_products
        dense_vector embedding
    }

    HYPOTHESIS_DOC {
        string tenant_id
        string hypothesis_id
        string statement
        string status
        float confidence
        string[] supporting_observations
        string[] contradicting_observations
        datetime updated_at
        dense_vector embedding
    }

    RAW_DOCUMENT ||--o{ OBSERVATION_DOC : contains
    COMPETITIVE_EVENT ||--o{ OBSERVATION_DOC : may_explain
    OBSERVATION_DOC ||--o{ HYPOTHESIS_DOC : supports
```

### 推奨Index

```text
cd_raw_documents
cd_observations
cd_competitive_events
cd_hypotheses
cd_reports
```

### 必須フィールド

各Indexには、最低限以下を持たせます。

| フィールド | 用途 |
|---|---|
| tenant_id | マルチテナント分離 |
| source_uri | 原文証跡へのリンク |
| source_type | 商談、日報、競合記事などの分類 |
| observed_at / created_at | 時系列検索 |
| entity_tags | 顧客、商品、競合、課題などのタグ |
| confidence | LLM抽出結果の信頼度 |
| body / summary / raw_quote | 検索・根拠提示 |
| embedding | ハイブリッド検索・類似検索 |

## 7. 検索方式の使い分け

```mermaid
flowchart TB
    Q["検索要求"] --> T{"何を探したいか？"}

    T -->|"語句が明確<br/>競合名・商品名・顧客名・条項・エラーコード"| ES1["Elasticsearch<br/>BM25 / フィルタ / ファセット"]

    T -->|"意味が近い発言<br/>似た失注理由・類似課題"| ES2["Elasticsearch Hybrid<br/>BM25 + Vector"]
    T -->|"大規模RAGで安定運用"| V1["Vertex AI Vector Search"]

    T -->|"関係をたどる<br/>顧客属性→課題→KPI→競合"| G1["BigQuery Graph / Spanner Graph"]

    T -->|"集計したい<br/>前週比・顧客数・時系列"| BQ1["BigQuery"]

    ES1 --> A["Gemini回答生成"]
    ES2 --> A
    V1 --> A
    G1 --> A
    BQ1 --> A
```

## 8. Agent別の利用ストア

```mermaid
flowchart TB
    subgraph Agents["Agent群"]
        S["Discovery Setup Agent"]
        R["Research Agent"]
        CI["Competitive Intelligence Agent"]
        KC["Knowledge Curator Agent"]
        KF["Knowledge Formation Agent"]
        O["Observation Agent"]
        D["Discovery Agent"]
        SC["Strategy Copilot Agent"]
        ET["Execution Tracking Agent"]
    end

    subgraph Stores["知識・検索ストア"]
        Wiki["LLM Wiki<br/>必須知識・観測方針"]
        ES["Elasticsearch<br/>原文検索・探索・Hybrid Search"]
        BQ["BigQuery<br/>構造化事実・KPI"]
        KG["BigQuery Graph / Spanner Graph<br/>関係性"]
        GCS["Cloud Storage<br/>原文証跡"]
    end

    S --> Wiki
    S --> BQ

    R --> ES
    R --> BQ
    R --> KC

    CI --> ES
    CI --> BQ
    CI --> KC

    KC --> BQ
    KC --> ES
    KC --> KF

    KF --> KG
    KF --> Wiki
    KF --> BQ

    O --> Wiki
    O --> BQ
    O --> R

    D --> BQ
    D --> KG
    D --> ES
    D --> Wiki

    SC --> Wiki
    SC --> ES
    SC --> KG
    SC --> BQ

    ET --> BQ
    ET --> Wiki

    GCS --> ES
```

## 9. 役割分担

| レイヤー | 推奨サービス | 役割 |
|---|---|---|
| 原文保管 | Cloud Storage | 原文証跡、音声、PDF、HTML、CSVの正本 |
| 前処理 | Cloud Run / Document AI / Speech-to-Text | クロール、抽出、文字起こし |
| PII対策 | Sensitive Data Protection | 個人情報・機密情報の検出、マスキング |
| LLM抽出 | Vertex AI Gemini | Observation / Entity / Relationship / Hypothesis抽出 |
| 原文検索 | Elasticsearch | 全文検索、ファセット検索、ハイブリッド検索 |
| 意味検索 | Elasticsearch Hybrid または Vertex AI Vector Search | 類似発言、類似事例、RAG |
| 構造化分析 | BigQuery | 観測事実、KPI、時系列、集計 |
| 関係分析 | BigQuery Graph / Spanner Graph | 顧客属性、課題、商品、競合、KPIの関係探索 |
| LLM Wiki | Cloud Storage / Git Repo | 企業概要、KPI定義、重点観測方針、重要仮説 |
| BI | Looker / Looker Studio | KPI、変化検知、週次/月次レポート |
| 対話UI | Custom Web UI | Strategy Copilot、Graph Viewer、Search Console |

## 10. MVP構成

初期MVPでは、Vertex AI Vector Searchを必須にせず、Elasticsearchのハイブリッド検索で代替してもよいです。

```text
Cloud Storage:
  原文の正本

Elasticsearch:
  原文検索、発言検索、競合情報検索、Hybrid Search

BigQuery:
  構造化Observation、Entity、Relationship、Hypothesis、KPI

BigQuery Graph:
  顧客属性 × 課題 × 商品 × 競合 × KPI の関係分析

LLM Wiki:
  企業概要、用語、KPI定義、重点観測方針、重要仮説

Vertex AI Gemini:
  抽出、分類、要約、仮説生成、レポート生成

Looker / Custom UI:
  KPI・変化検知・ナレッジグラフ・検索UI
```

## 11. 代表的な検索ユースケース

### 11.1 価格関連発言を探す

```text
条件:
- tenant_id = company_a
- source_type = sales_conversation
- observed_at >= now - 30d
- body contains "価格" OR "高い" OR "他社"
- customer_segment = small_retail
```

### 11.2 競合Aに関する最近の兆候を探す

```text
条件:
- competitor = 競合A
- source_type IN competitive_news, job_posting, sales_conversation
- observed_at >= now - 60d
```

### 11.3 類似失注理由を探す

```text
入力:
- "価格は問題ないが、導入後のサポート体制が不安で失注した"

検索:
- Elasticsearch Hybrid Search
- または Vertex AI Vector Search

出力:
- 類似した過去商談
- 類似顧客属性
- 関連商品
- 過去施策
```

## 12. 設計上の注意点

### 12.1 Elasticsearchを正本にしない

Elasticsearchは検索・探索に強い一方、分析の正本や監査証跡の正本にはしない方がよいです。

```text
正本:
Cloud Storage / BigQuery / LLM Wiki

探索:
Elasticsearch

関係分析:
BigQuery Graph / Spanner Graph

生成AI:
Vertex AI Gemini
```

### 12.2 事実と仮説を分離する

```text
事実:
小規模小売顧客から価格関連発言が31件あった

仮説:
競合Aの値下げが原因かもしれない
```

事実と仮説を同じIndexに混在させる場合でも、`doc_type` や `status` を明確に分ける必要があります。

### 12.3 すべての知識に証拠を持たせる

`entity`、`relationship`、`hypothesis`、`report_sentence` には、最低限以下を紐づけます。

```text
source_id
source_uri
raw_quote
confidence
created_by_agent
review_status
```

### 12.4 テナント分離

マルチテナントSaaSを想定する場合、以下を必須にします。

```text
- tenant_id による論理分離
- Index alias または tenant別Indexの設計
- BigQuery Row-level security
- Cloud Storage bucket/prefix分離
- IAM最小権限
- PIIマスキング
- 監査ログ
```

## 13. 推奨結論

Elasticsearchを一部活用する場合の最適な考え方は、次の通りです。

> Elasticsearchは「企業の記憶の正本」ではなく、「企業の記憶を探索する検索エンジン」として置く。

この構成にすると、Google Cloud側の生成AI、分析、グラフ、BIの役割は崩れません。むしろ、以下の2つが強化されます。

1. 現場・コンサルタントが原文を直接探索する体験
2. LLMエージェントが根拠を取りに行く検索体験

したがって、Continuous Discovery Agentのサービス構成は、以下の分担が最も現実的です。

```text
Cloud Storage:
  原文証跡

Elasticsearch:
  全文検索、ファセット検索、ハイブリッド検索

BigQuery:
  構造化された観測事実、KPI、仮説、施策

BigQuery Graph / Spanner Graph:
  顧客属性、課題、商品、競合、KPIの関係探索

LLM Wiki:
  企業概要、用語、KPI定義、重点観測方針、重要仮説

Vertex AI Gemini:
  抽出、分類、要約、仮説生成、レポート生成

Looker / Custom UI:
  KPIダッシュボード、ナレッジグラフ、検索UI、Strategy Copilot
```

## 14. 参考情報

- Elastic Cloud from Google Cloud Platform Marketplace: https://www.elastic.co/docs/deploy-manage/deploy/elastic-cloud/google-cloud-platform-marketplace
- Elasticsearch Hybrid Search: https://www.elastic.co/elasticsearch/hybrid-search
- Google Cloud: RAG infrastructure for generative AI using Vertex AI and Vector Search: https://docs.cloud.google.com/architecture/gen-ai-rag-vertex-ai-vector-search
- Google Cloud: Introduction to BigQuery Graph: https://docs.cloud.google.com/bigquery/docs/graph-overview
