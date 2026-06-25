# 背景と参照ソース

## 背景

企業の重要情報は、CRMや会計システムだけではなく、事業主の頭の中、従業員の経験、顧客との会話、商談中の雑談、競合に関する噂や外部環境の変化に存在する。

Continuous Discovery Agentは、これらの定性的・非構造情報を継続的に収集し、企業固有のナレッジとして構造化し、KPI・重点管理指標・観測シグナルを設計するためのプラットフォームである。

## Google Cloud / ADK関連

- Vertex AI Agent Builder: 本番環境でAIエージェントを構築、スケール、管理するためのGoogle Cloud製品群。
  - https://docs.cloud.google.com/agent-builder
- Google Agent Development Kit（ADK） + Vertex AI + GKEのチュートリアルでは、ADKがAIエージェントの開発・デプロイ向けの柔軟なモジュール型フレームワークであること、Vertex AIをLLMプロバイダとして利用できることが説明されている。
  - https://docs.cloud.google.com/kubernetes-engine/docs/tutorials/agentic-adk-vertex?hl=ja

## BigQuery関連

- BigQueryのマルチテナントワークロードのベストプラクティスでは、テナントごとにデータセットを構成する方式が説明されている。
  - https://docs.cloud.google.com/bigquery/docs/best-practices-for-multi-tenant-workloads-on-bigquery
- BigQueryのスキーマ管理では、列追加などの変更方法や制約が説明されている。
  - https://docs.cloud.google.com/bigquery/docs/managing-table-schemas
- BigQuery DMLは、INSERT/UPDATE/DELETE/MERGEによるデータ操作に利用できる。
  - https://docs.cloud.google.com/bigquery/docs/data-manipulation-language
- Dataformは、BigQueryのデータ変換ワークフローを開発、テスト、バージョン管理、スケジュールするためのサービス。
  - https://docs.cloud.google.com/dataform/docs/overview

## Cloud Storage関連

- Cloud Storage Object Versioningは、オブジェクトの過去世代を保持できる。
  - https://docs.cloud.google.com/storage/docs/object-versioning
- Object Lifecycle Managementは、古いオブジェクトや非現行バージョンの自動削除/移行に利用できる。
  - https://docs.cloud.google.com/storage/docs/lifecycle

