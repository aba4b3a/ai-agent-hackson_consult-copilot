# Implementation Plan: Continuous Discovery Agent MVP

## 1. Purpose

This `tasks.md` translates `requirements.md` and `design.md` into implementation work items for a Kiro-like build flow.

The implementation plan assumes the following artifact sequence:

```text
requirements.md
  -> design.md
  -> tasks.md
  -> implementation
```

The MVP is designed for a hackathon-scale build. It prioritizes rapid knowledge formation, evidence search, consultant-facing discovery workflows, and visible knowledge accumulation over enterprise-grade correctness, privacy hardening, or low-latency graph traversal.

## 2. Implementation Principles

1. Preserve the core product loop:

   ```text
   Observation
   -> Knowledge Formation
   -> Discovery
   -> Hypothesis
   -> Additional Observation
   -> Organizational Learning
   ```

2. Separate observed facts from hypotheses in data model, UI, and reports.
3. Store AI-extracted knowledge directly without mandatory review in the MVP.
4. Allow later correction, supersession, or deprecation of extracted knowledge.
5. Use BigQuery as the analytical source of truth.
6. Use Elasticsearch only for source search, evidence retrieval, faceted exploration, and optional hybrid search.
7. Use BigQuery Graph for relationship analysis and accept slower graph query latency.
8. Do not use Spanner or Spanner Graph in the MVP.
9. Keep logical agents to four groups:
   - Intake Agent
   - Knowledge Agent
   - Discovery Agent
   - Report Copilot
10. Build consultant-facing dashboard, knowledge formation, graph visualization, and report copilot screens.
11. Build business-side information collection as a lightweight URL form and conversational voice intake experience.

## 3. Out of Scope for This Task Plan

- Spanner / Spanner Graph implementation.
- Low-latency operational graph traversal.
- Full CRM, Slack, Teams, Google Workspace, or email integration.
- Production-grade privacy and compliance controls.
- Advanced ML-based anomaly detection.
- Strict human approval workflow before extracted knowledge becomes usable.
- Automated business decisions or action execution.

> Design note: Spanner Graph can be reconsidered later if operational graph traversal latency becomes a product requirement. The MVP intentionally uses BigQuery Graph due to cost constraints.

## 4. Suggested Milestones

| Milestone | Goal | Demo Value |
|---|---|---|
| M1 Foundation | App shell, cloud resources, schema, mock data | Project is runnable end-to-end with static data |
| M2 Intake | URL form, voice/chat intake, source persistence | Business-side data can be collected |
| M3 Knowledge Formation | Gemini extraction, BigQuery insert, Elasticsearch index | Raw information becomes structured knowledge |
| M4 Discovery | Rule-based signals, report generation | Changes and hypotheses are surfaced |
| M5 Consultant UI | Dashboard, knowledge formation, graph viewer, report copilot | Value is visible to consultants |
| M6 Demo Polish | Seed data, scenario, error handling, README | Hackathon presentation is coherent |

---

# Tasks

## 1. Project Foundation

- [x] 1.1 Create the monorepo or application repository structure
  - Create `apps/web` for the Next.js application.
  - Create `apps/api` or `services/api` for Cloud Run API handlers if separated from Next.js route handlers.
  - Create `services/workers` for ingestion, extraction, indexing, discovery, and report generation workers.
  - Create `infra` for deployment scripts and environment templates.
  - Create `docs` for requirements, design, tasks, architecture notes, and demo scenarios.
  - _Requirements: R19, R20_
  - _Note: 既存の標準レイアウト `front/` `back/` `agent/` `infra/` `docs/`（AGENTS.md/DESIGN.md 準拠）で充足。`apps/web`/`services/*` への再編は行わない。_

- [x] 1.2 Configure Next.js, TypeScript, Tailwind CSS, and base UI conventions
  - Initialize Next.js with TypeScript.
  - Configure Tailwind CSS.
  - Define mobile-first layout primitives: app shell, sticky header, card, bottom navigation, pill tabs, list item, metric card, graph card, chat bubble.
  - Define design tokens for background, surface, border, text, accent, success, warning, and danger states.
  - Ensure screens are usable as vertically scrolling mobile web views.
  - _Requirements: R14, R15, R16, R19_

- [x] 1.3 Create environment configuration
  - Define `.env.example` for local development.
  - Include placeholders for Google Cloud project ID, Cloud Storage bucket, BigQuery dataset, Elasticsearch endpoint, Gemini model, and service credentials.
  - Add runtime validation for required environment variables.
  - _Requirements: R19, R20_

- [x] 1.4 Create local mock mode
  - Implement a mock data provider for sources, observations, entities, relationships, discovery signals, and reports.
  - Allow the UI to run without live Google Cloud or Elasticsearch dependencies.
  - Use mock mode for early UI and demo development.
  - _Requirements: R19_

---

## 2. Cloud Resource Setup

- [ ] 2.1 Create Cloud Storage bucket structure
  - Create folder prefixes for `raw/`, `processed/`, `wiki/`, `reports/`, and `exports/`.
  - Store uploaded documents, submitted report payloads, voice transcription artifacts, and generated wiki pages.
  - Persist `source_uri` for every stored source object.
  - _Requirements: R4, R10_

- [ ] 2.2 Create BigQuery dataset
  - Create a dataset such as `continuous_discovery`.
  - Define table creation scripts for all MVP tables.
  - Include `workspace_id`, `created_at`, and `updated_at` on all core tables.
  - _Requirements: R7, R19_

- [ ] 2.3 Create BigQuery core tables
  - Create `workspaces`.
  - Create `sources`.
  - Create `observations`.
  - Create `entities`.
  - Create `relationships`.
  - Create `hypotheses`.
  - Create `discovery_signals`.
  - Create `kpi_definitions`.
  - Create `kpi_snapshots`.
  - Create `reports`.
  - Create `corrections`.
  - _Requirements: R5, R6, R7, R11, R13, R17, R18_

- [ ] 2.4 Create BigQuery Graph definitions or graph-compatible views
  - Prepare node views from `entities`, `observations`, `hypotheses`, `kpi_definitions`, and `discovery_signals`.
  - Prepare edge views from `relationships` and derived evidence links.
  - Ensure graph slices can be queried by customer segment, issue, product, competitor, KPI, and hypothesis.
  - _Requirements: R9, R14_

- [ ] 2.5 Create Elasticsearch indexes
  - Create `cd_sources` for source documents and evidence search.
  - Create `cd_observations` for extracted observations and snippets.
  - Optionally create `cd_reports` for searching generated reports.
  - Include fields for `workspace_id`, `source_id`, `source_type`, `title`, `body`, `summary`, `tags`, `entities`, `customer_segments`, `products`, `competitors`, `observed_at`, and `source_uri`.
  - Add vector fields only if hybrid retrieval is implemented in the MVP.
  - _Requirements: R8, R15_

- [ ] 2.6 Create Pub/Sub topics or equivalent event routes
  - Create `source-created`.
  - Create `source-processed`.
  - Create `knowledge-extracted`.
  - Create `report-requested`.
  - Use direct API invocation instead if Pub/Sub setup is too heavy for the hackathon, but keep event names in code boundaries.
  - _Requirements: R4, R5, R13, R19_

---

## 3. Workspace Setup and Consultant Onboarding

> _M2 Note: 永続化は back の in-memory モックで代替（実 BigQuery / LLM Wiki は後続）。詳細は design.md §23。_

- [x] 3.1 Implement workspace setup API
  - Create `POST /api/workspaces`.
  - Accept company name, business description, products/services, customer segments, competitors, known issues, KPIs, and initial observation policy.
  - Store setup data in BigQuery.
  - Generate initial LLM Wiki pages in Cloud Storage.
  - _Requirements: R1, R10, R12_

- [x] 3.2 Implement consultant-facing setup screen
  - Build a mobile-first setup flow for consultants.
  - Include sections for company profile, customer segments, products, competitors, KPIs, and priority observation topics.
  - Show a setup completion summary.
  - _Requirements: R1, R12_

- [ ] 3.3 Generate initial knowledge map from setup input
  - Create initial `entities` for customer segments, products, competitors, KPIs, and issues.
  - Create initial `relationships` such as customer segment to product, product to KPI, competitor to product, and issue to KPI where provided.
  - Mark setup-derived knowledge with `source_type = setup`.
  - _Requirements: R1, R5, R9, R10_

- [ ] 3.4 Create initial observation policy file
  - Write `wiki/observation_policy.md`.
  - Include priority topics, target customer segments, known competitors, KPIs, and follow-up guidance.
  - Use this page as context for extraction and report generation prompts.
  - _Requirements: R10, R12_

---

## 4. Business-Side URL Report Form

> _M2 Note: URL は Static Export のためクエリ方式 `/intake?form=<id>`。取得用に `GET /report-forms/{id}` を追加。永続化は in-memory モック。詳細は design.md §23。_

- [x] 4.1 Implement report form creation API
  - Create `POST /api/report-forms`.
  - Generate a shareable URL for a specific workspace and report context.
  - Allow consultant to specify target respondent role, focus topics, and due date.
  - _Requirements: R2, R12_

- [x] 4.2 Implement URL-based daily report form UI
  - Build a simple mobile-first form intended for business-side users.
  - Include fields for free text, customer type, product/service, issue category, competitor mention, and optional KPI note.
  - Make the form accessible without exposing consultant dashboard features.
  - _Requirements: R2_

- [x] 4.3 Add guided prompts to the report form
  - Display targeted questions based on the current observation policy.
  - Prefer a small number of high-value questions.
  - Allow users to skip questions.
  - Prioritize information capture over perfect UX minimalism.
  - _Requirements: R2, R12_

- [x] 4.4 Implement report form submission API
  - Create `POST /api/report-submissions`.
  - Persist submitted content to Cloud Storage.
  - Create a `sources` row in BigQuery.
  - Trigger or enqueue extraction.
  - _Requirements: R2, R4, R5_

---

## 5. Conversational Voice Intake

> _M2 Note: テキスト会話インテークで実装（`/intake/chat`）。実音声 STT/TTS（5.2/5.3）は後続。requirements.md R3 の Implementation Note 参照。_
> _更新: 5.4 のフォローアップは固定文から **Gemini 動的生成**（観測方針ベース）に変更（R12.4 準拠、スキップ可）。詳細は design.md §23.7。_

- [x] 5.1 Implement voice intake screen for business-side users
  - Build a chat-like mobile UI with assistant prompts, user responses, transcript bubbles, and recording controls.
  - Include states for listening, transcribing, assistant speaking, and saving.
  - Make it clear that the conversation is for field knowledge collection.
  - _Requirements: R3, R12_

- [ ] 5.2 Implement speech-to-text integration or browser speech fallback
  - Use a server-side transcription flow if available.
  - Otherwise, implement a browser speech recognition fallback for demo purposes.
  - Persist transcript text as the source body.
  - _Requirements: R3, R4_

- [ ] 5.3 Implement text-to-speech or assistant prompt playback
  - Add assistant prompt playback for conversational intake.
  - Allow users to read prompts as text if audio playback is unavailable.
  - Keep prompt turns concise and focused on missing business context.
  - _Requirements: R3, R12_

- [x] 5.4 Implement conversational follow-up logic
  - Ask follow-up questions when user input is too vague, such as "busy today" or "many inquiries".
  - Ask about cause, difference from usual, customer characteristics, product/service, competitor mention, and business impact.
  - Stop after a bounded number of turns to avoid excessive friction.
  - _Requirements: R2, R3, R12_

- [x] 5.5 Persist voice intake as a source
  - Save transcript, prompt turns, and metadata to Cloud Storage.
  - Create a corresponding `sources` row.
  - Trigger or enqueue extraction.
  - _Requirements: R3, R4, R5_

---

## 6. Source Data Ingestion

- [ ] 6.1 Implement generic source upload API
  - Create `POST /api/sources`.
  - Accept text, markdown, CSV, or simple file uploads.
  - Store raw content in Cloud Storage.
  - Create `sources` metadata in BigQuery.
  - _Requirements: R4_

- [ ] 6.2 Implement consultant note input
  - Add a consultant-only screen or modal for adding notes from interviews, meetings, or observations.
  - Persist notes as `source_type = consultant_note`.
  - Trigger extraction.
  - _Requirements: R4, R5_

- [ ] 6.3 Implement simple competitive intelligence input
  - Allow consultants to paste a competitor URL, article text, press release summary, recruitment post, or news summary.
  - Store as `source_type = competitive_intelligence`.
  - Trigger extraction with competitor-focused schema hints.
  - _Requirements: R4, R5, R11_

- [ ] 6.4 Implement KPI CSV upload or manual KPI entry
  - Allow consultants to upload simple KPI snapshots or enter values manually.
  - Store KPI values in `kpi_snapshots`.
  - Link KPI definitions to workspace setup data.
  - _Requirements: R18_

---

## 7. Gemini-Based Knowledge Extraction

- [x] 7.1 Define structured extraction schema
  - Define JSON schema for observations, entities, relationships, hypotheses, evidence snippets, and recommended follow-up topics.
  - Include `type`, `name`, `summary`, `confidence`, `source_id`, `evidence_quote`, and `fact_or_hypothesis` fields where appropriate.
  - _Requirements: R5, R6_

- [x] 7.2 Implement extraction prompt builder
  - Load source text.
  - Load workspace profile and observation policy from BigQuery or LLM Wiki.
  - Add rules that observed facts and hypotheses must be separated.
  - Add rules that extraction should prioritize useful knowledge formation over perfect certainty.
  - _Requirements: R5, R6, R10, R12_

- [x] 7.3 Implement Knowledge Agent extraction worker
  - Call Gemini with the structured schema.
  - Parse and validate returned JSON.
  - Store raw extraction output for debugging.
  - Handle partial extraction results gracefully.
  - _Requirements: R5, R6_
  - _Note: agent が Gemini 構造化出力(response_schema=ExtractionPayload)で呼び出し・検証・partial/失敗時フォールバックを実装。back は `use_agent_extraction` で経路を切替（design.md §23.6）。raw 出力保存は後続。_

- [ ] 7.4 Implement entity normalization
  - Match extracted entities to existing entities by workspace, type, normalized name, and aliases.
  - Create new entities when no clear match exists.
  - Keep logic lightweight and tolerant of duplicates for the MVP.
  - _Requirements: R5, R7_

- [ ] 7.5 Implement relationship creation
  - Convert extracted relationships into BigQuery `relationships` rows.
  - Include `from_entity_id`, `to_entity_id`, `relationship_type`, `strength`, `evidence_count`, `first_seen_at`, and `last_seen_at` when available.
  - Allow relationship strength to be approximate.
  - _Requirements: R5, R7, R9_

- [ ] 7.6 Implement hypothesis creation
  - Store hypotheses separately from observations.
  - Link hypotheses to supporting and contradicting observations where available.
  - Include status such as `observing`, `supported`, `weakened`, or `superseded`.
  - _Requirements: R6, R7, R11_

- [ ] 7.7 Implement evidence preservation
  - Store evidence quotes in observations or evidence metadata.
  - Ensure each reportable finding can trace back to at least one source or quote when available.
  - Do not block storage if evidence quote is missing in the MVP; mark it as lower confidence.
  - _Requirements: R5, R8, R13, R20_

---

## 8. BigQuery Persistence Layer

- [ ] 8.1 Implement BigQuery repository module
  - Add insert and query functions for workspaces, sources, observations, entities, relationships, hypotheses, discovery signals, KPI snapshots, reports, and corrections.
  - Keep SQL centralized and testable.
  - _Requirements: R7_

- [ ] 8.2 Implement source persistence
  - Insert source metadata after upload or form submission.
  - Track processing status: `created`, `processing`, `extracted`, `indexed`, `failed`.
  - _Requirements: R4, R7_

- [ ] 8.3 Implement extracted knowledge persistence
  - Insert observations, entities, relationships, and hypotheses from extraction output.
  - Preserve workspace and source linkage.
  - _Requirements: R5, R6, R7_

- [ ] 8.4 Implement KPI persistence
  - Insert and query KPI definitions.
  - Insert and query KPI snapshots.
  - Support at least weekly comparison for MVP reporting.
  - _Requirements: R18_

- [ ] 8.5 Implement correction and supersession persistence
  - Create endpoint and repository function for corrections.
  - Allow observations, entities, relationships, and hypotheses to be corrected or superseded.
  - Keep original records for audit-like visibility in the MVP.
  - _Requirements: R17_

---

## 9. Elasticsearch Indexing and Retrieval

- [ ] 9.1 Implement Elasticsearch client module
  - Configure connection, authentication, index names, and basic error handling.
  - Add health check function.
  - _Requirements: R8, R15_

- [ ] 9.2 Implement source indexing
  - Index source title, body, summary, metadata, tags, extracted entities, and source URI.
  - Include workspace and source type filters.
  - _Requirements: R8, R15_

- [ ] 9.3 Implement observation indexing
  - Index observation summary, evidence quote, issue type, customer segment, product, competitor, confidence, and observed date.
  - Keep BigQuery as source of truth and Elasticsearch as search copy.
  - _Requirements: R8, R15_

- [ ] 9.4 Implement evidence search API
  - Create `GET /api/search/evidence`.
  - Support keyword query, source type filter, date filter, customer segment filter, product filter, competitor filter, and issue filter.
  - Return source snippets and evidence links.
  - _Requirements: R8, R15, R16_

- [ ] 9.5 Implement retrieval mode routing
  - Use Elasticsearch for text and evidence search.
  - Use BigQuery for aggregation and KPI analysis.
  - Use BigQuery Graph for relationship exploration.
  - If a retrieval use case appears fully covered by both BigQuery and Elasticsearch, document the decision and prefer the store aligned with primary purpose.
  - _Requirements: R8, R9, R15, R19_

- [ ] 9.6 Implement optional hybrid search
  - Generate embeddings for source or observation snippets if feasible.
  - Add vector fields to Elasticsearch indexes.
  - Combine lexical and semantic retrieval for evidence search.
  - Keep this optional if time is limited.
  - _Requirements: R8, R15, R19_

---

## 10. LLM Wiki Writer

- [ ] 10.1 Implement wiki storage writer
  - Write Markdown files to `wiki/` in Cloud Storage or local demo storage.
  - Generate deterministic file names for company profile, customer segments, products, competitors, KPIs, observation policy, discovery log, and hypothesis register.
  - _Requirements: R10, R12_

- [ ] 10.2 Implement company profile page generation
  - Write `company_profile.md` from setup input.
  - Include business description, customer segments, product/service summary, competitors, known issues, and KPIs.
  - _Requirements: R1, R10_

- [ ] 10.3 Implement knowledge formation summary pages
  - Write or update `customer_segments.md`, `products.md`, `competitors.md`, `known_issues.md`, and `hypothesis_register.md`.
  - Summaries may be AI-generated and approximate in the MVP.
  - _Requirements: R10_

- [ ] 10.4 Implement discovery log page
  - Append weekly discovery signals, facts, hypotheses, and recommended observation topics to `discovery_log.md`.
  - Clearly label facts and hypotheses.
  - _Requirements: R6, R10, R13_

---

## 11. Rule-Based Discovery Detection

> _in-memory 実装（design.md §23.9）。BigQuery SQL 化はフェーズ2。閾値はコード内定数（ワークスペース別設定 R11.9 は後続）。_

- [x] 11.1 Implement discovery threshold configuration
  - Define default thresholds for weekly increase, four-week average deviation, new competitor mention, recurring issue count, and KPI-linked signal.
  - Store thresholds in code or a lightweight configuration table.
  - _Requirements: R11, R18_

- [x] 11.2 Implement weekly count aggregation
  - Aggregate observations by week, customer segment, issue type, product, competitor, and source type.
  - Compute previous week count and percentage change.
  - _Requirements: R11_

- [x] 11.3 Implement four-week baseline comparison
  - Compute recent count against trailing four-week average.
  - Create signals when thresholds are exceeded.
  - _Requirements: R11_

- [x] 11.4 Implement new entity and competitor mention detection
  - Detect newly appearing competitors, issues, or customer needs.
  - Link detected signals to source observations and entities.
  - _Requirements: R11_

- [ ] 11.5 Implement KPI-linked signal detection <!-- KPIスナップショット（6.4）が前提のため後続 -->
  - Compare discovery signals with KPI snapshots where available.
  - Do not infer causality as fact.
  - Store KPI relationship as hypothesis or possible association.
  - _Requirements: R6, R11, R18_

- [x] 11.6 Persist discovery signals
  - Insert generated signals into `discovery_signals`.
  - Include severity, signal type, affected segment, related issue/product/competitor/KPI, and evidence references.
  - _Requirements: R11, R13_

---

## 12. BigQuery Graph Analysis

- [ ] 12.1 Implement graph slice query module
  - Query graph-compatible views for selected center node and graph type.
  - Support graph types such as customer-issue, competitor-impact, KPI-causal, hypothesis, and knowledge-gap.
  - _Requirements: R9, R14_

- [ ] 12.2 Implement graph slice API
  - Create `GET /api/graph/slice`.
  - Accept workspace, graph type, center entity, date range, and limit parameters.
  - Return nodes and edges formatted for frontend graph rendering.
  - _Requirements: R9, R14_

- [ ] 12.3 Implement graph summarization
  - Generate a short plain-language summary of the graph slice.
  - Separate observed relationships from hypothesis relationships.
  - _Requirements: R6, R9, R14_

- [ ] 12.4 Implement graph latency fallback
  - Add loading, timeout, and cached/mock fallback behavior in UI.
  - Make clear that BigQuery Graph analysis may be slower than operational graph databases.
  - _Requirements: R9, R14, R20_

---

## 13. Weekly Discovery Report

> _Gemini 化済み（design.md §23.9）。オンデマンド生成（scheduler/worker 化は後続）、retrieval は in-memory、証拠は back が付与、失敗時はテンプレにフォールバック。_

- [x] 13.1 Implement report generation worker
  - Load discovery signals, observations, hypotheses, KPI snapshots, graph summaries, and evidence snippets for the target week.
  - Call Gemini to generate report content.
  - Store report in BigQuery and optionally Markdown in Cloud Storage.
  - _Requirements: R13, R18_

- [x] 13.2 Implement report prompt
  - Require sections for summary, discovery signals, observed facts, hypotheses, evidence, related graph relationships, recommended observation topics, and limitations.
  - Forbid presenting hypotheses as facts.
  - Forbid direct business decision execution.
  - _Requirements: R6, R13, R20_

- [x] 13.3 Implement report retrieval API
  - Create `GET /api/reports/weekly`.
  - Return latest report or report by week.
  - Include links to related observations, sources, and graph slices.
  - _Requirements: R13, R16_

- [x] 13.4 Implement report regeneration API
  - Create `POST /api/reports/weekly/generate`.
  - Allow consultant to regenerate report after new sources or KPI data are added.
  - _Requirements: R13_

---

## 14. Report Copilot

> _Gemini 化済み（design.md §23.8）。retrieval は in-memory 代替（ES/BQ は後続）、証拠は back が付与、失敗時は定型回答にフォールバック。_

- [x] 14.1 Implement copilot question API
  - Create `POST /api/copilot/ask`.
  - Accept question, workspace, optional report ID, and optional context filters.
  - _Requirements: R16_

- [x] 14.2 Implement retrieval pipeline for copilot
  - Retrieve relevant evidence from Elasticsearch.
  - Retrieve related facts, hypotheses, KPI values, and graph relationships from BigQuery.
  - Retrieve observation policy and relevant wiki snippets.
  - _Requirements: R8, R9, R10, R16_
  - _Note: in-memory から facts/hypotheses/evidence/観測方針を集約（ES/BQ 実接続は後続）。_

- [x] 14.3 Implement grounded answer generation
  - Answer as a consultant-facing assistant.
  - Separate observed facts, hypotheses, and recommended observations.
  - Include evidence snippets when available.
  - Avoid making business decisions for the user.
  - _Requirements: R6, R16, R20_

- [x] 14.4 Implement copilot UI
  - Build mobile-first chat interface for consultants.
  - Include suggested questions such as "なぜ価格関連発言が増えた？", "どの顧客セグメントで変化が大きい？", and "来週何を観測すべき？".
  - Show citations or evidence chips linking to source snippets.
  - _Requirements: R16_

---

## 15. Consultant-Facing Dashboard UI

- [ ] 15.1 Build consultant home dashboard
  - Show active client/workspace selector.
  - Show discovery feed, new signals, unresolved hypotheses, and latest weekly report summary.
  - Include quick links to Knowledge Formation, Graph Viewer, Evidence Search, and Report Copilot.
  - _Requirements: R13, R14, R15, R16_

- [ ] 15.2 Build knowledge formation screen
  - Show knowledge accumulation status: sources ingested, observations extracted, entities formed, relationships created, hypotheses under observation, and evidence coverage.
  - Show recent knowledge additions grouped by customer segment, product, issue, competitor, and KPI.
  - Show knowledge gaps and recommended additional observations.
  - _Requirements: R5, R10, R12, R14_

- [ ] 15.3 Build knowledge quality and correction affordances
  - Allow consultant to mark extracted items as useful, incorrect, duplicate, or superseded.
  - Keep correction lightweight and optional.
  - Emphasize speed of knowledge formation over strict review.
  - _Requirements: R17, R20_

- [ ] 15.4 Build knowledge graph viewer screen
  - Support graph tabs: Customer x Issue, Competitor Impact, KPI Causal, Hypothesis, and Gap Graph.
  - Show mobile-friendly graph cards, mini network views, relationship lists, and key node summaries.
  - Allow graph filter by segment, product, competitor, KPI, and date range.
  - _Requirements: R9, R14_

- [ ] 15.5 Build search and evidence screen
  - Provide keyword search box and filters.
  - Show evidence snippets, source type, source date, related entities, and confidence.
  - Allow opening source detail.
  - _Requirements: R8, R15_

- [x] 15.6 Build weekly report screen
  - Display report sections in vertically stacked cards.
  - Clearly separate facts, hypotheses, evidence, and recommended observations.
  - Include related graph and evidence links.
  - _Requirements: R6, R13, R16_
  - _Note: summary / 推奨観測 / limitations / 再生成ボタンを表示。事実・仮説は Knowledge Formation セクションで分離表示済み。グラフリンクは §15.4 と併せて後続。_

---

## 16. Business-Side Intake UI Refinement

- [x] 16.1 Separate business-side intake from consultant dashboard
  - Ensure URL form and voice intake do not expose dashboard, graph, search, or copilot views.
  - Use role-appropriate labels for field users.
  - _Requirements: R2, R3, R20_

- [x] 16.2 Make voice intake feel conversational
  - Use assistant prompt bubbles and user response bubbles.
  - Support both tap-to-record and text fallback.
  - Show extracted temporary summary before submission.
  - _Requirements: R3, R12_
  - _M2 Note: 会話バブルと送信前の内容確認は実装済み。フォローアップは Gemini 動的生成 + スキップ可（R12.8）。tap-to-record（音声録音）は 5.2 と併せて後続。_

- [x] 16.3 Add consultant-generated intake links
  - Allow consultant to generate a URL for a specific observation topic.
  - Include focus topics in the intake prompt sequence.
  - _Requirements: R2, R12_
  - _M2 Note: ダッシュボードの「Intake link」で共有URLを生成。トピック指定（focus topics のUI選択）は後続で、現状は既定質問を使用。_

---

## 17. API Integration and End-to-End Flows

- [ ] 17.1 Implement end-to-end flow: setup to initial knowledge
  - Create workspace.
  - Generate initial wiki pages.
  - Insert initial entities and relationships.
  - Display consultant dashboard with initial knowledge state.
  - _Requirements: R1, R5, R10, R14_

- [ ] 17.2 Implement end-to-end flow: daily report to knowledge
  - Submit URL report.
  - Store source.
  - Extract knowledge.
  - Insert BigQuery records.
  - Index Elasticsearch documents.
  - Update knowledge formation screen.
  - _Requirements: R2, R4, R5, R7, R8_

- [ ] 17.3 Implement end-to-end flow: voice conversation to discovery
  - Complete conversational intake.
  - Store transcript.
  - Extract observations and hypotheses.
  - Run rule-based discovery detection.
  - Show signal on consultant dashboard.
  - _Requirements: R3, R5, R6, R11_

- [ ] 17.4 Implement end-to-end flow: search to copilot answer
  - Search evidence.
  - Ask copilot about the evidence or report.
  - Generate answer with facts/hypotheses separated.
  - Show evidence chips.
  - _Requirements: R8, R15, R16, R20_

- [ ] 17.5 Implement end-to-end flow: graph to report
  - Generate graph slice.
  - Summarize relationships.
  - Include graph insights in weekly report.
  - _Requirements: R9, R13, R14_

---

## 18. Error Handling and Observability

- [ ] 18.1 Add processing status and error fields
  - Track status on sources, extraction jobs, indexing jobs, and report generation jobs.
  - Store last error message where appropriate.
  - _Requirements: R4, R5, R13_

- [ ] 18.2 Add retry behavior for workers
  - Retry transient Gemini, BigQuery, Elasticsearch, and storage failures.
  - Avoid duplicate records where possible by using idempotency keys.
  - _Requirements: R19, R20_

- [ ] 18.3 Add basic application logging
  - Log source ingestion, extraction, indexing, discovery, report generation, and copilot requests.
  - Include workspace and source IDs, but avoid verbose sensitive content in logs where practical.
  - _Requirements: R19, R20_

- [ ] 18.4 Add demo-friendly failure states
  - Show clear UI messages when extraction, graph query, report generation, or search fails.
  - Provide mock fallback data for hackathon demonstration if live service calls fail.
  - _Requirements: R19_

---

## 19. Demo Dataset and Scenario

- [ ] 19.1 Create demo workspace data
  - Define a fictional SME client.
  - Include customer segments, products, competitors, KPIs, known issues, and initial observation policy.
  - _Requirements: R1, R18_

- [ ] 19.2 Create sample daily reports and voice transcripts
  - Include vague inputs that trigger follow-up questions.
  - Include specific observations about price, competitor mentions, inquiries, complaints, and segment changes.
  - _Requirements: R2, R3, R4_

- [ ] 19.3 Create sample competitive intelligence sources
  - Include competitor campaign, recruitment, pricing, product launch, or press release examples.
  - _Requirements: R4, R11_

- [ ] 19.4 Create sample KPI snapshots
  - Include sales, repeat rate, average order value, churn, inquiry count, or lost deal count.
  - Include simple week-over-week changes for report demonstration.
  - _Requirements: R18_

- [ ] 19.5 Seed demo data into BigQuery and Elasticsearch
  - Provide seed scripts.
  - Ensure dashboard, graph viewer, search, and report screens have meaningful data.
  - _Requirements: R7, R8, R9, R13, R14, R15_

- [ ] 19.6 Prepare hackathon story script
  - Start with business-side voice intake.
  - Show knowledge formation accumulating.
  - Show graph relationships.
  - Show discovery signal.
  - Show weekly report.
  - Ask copilot a question.
  - _Requirements: R13, R14, R16_

---

## 20. Testing

- [ ] 20.1 Add unit tests for schema validation
  - Test extraction output validation.
  - Test fact/hypothesis separation fields.
  - Test required BigQuery insert payloads.
  - _Requirements: R5, R6, R7_

- [ ] 20.2 Add unit tests for discovery rules
  - Test weekly increase detection.
  - Test four-week baseline deviation.
  - Test new competitor mention detection.
  - Test KPI-linked signal generation without causal overstatement.
  - _Requirements: R6, R11, R18_

- [ ] 20.3 Add integration tests for core flows
  - Test report form submission to source creation.
  - Test source extraction to BigQuery insertion.
  - Test source indexing to Elasticsearch.
  - Test weekly report generation.
  - _Requirements: R2, R4, R5, R8, R13_

- [ ] 20.4 Add UI smoke tests or manual QA checklist
  - Check consultant dashboard.
  - Check knowledge formation screen.
  - Check graph viewer tabs.
  - Check business-side report form.
  - Check conversational voice intake.
  - Check report copilot.
  - _Requirements: R2, R3, R13, R14, R15, R16_

---

## 21. Deployment and Documentation

- [ ] 21.1 Create local development README
  - Document setup, environment variables, mock mode, and run commands.
  - Include how to seed demo data.
  - _Requirements: R19_

- [ ] 21.2 Create deployment notes
  - Document Cloud Run services, Cloud Storage bucket, BigQuery dataset, Elasticsearch deployment, and required secrets.
  - Include Spanner exclusion note and future consideration note.
  - _Requirements: R19, R20_

- [ ] 21.3 Create API documentation
  - Document workspace setup, report form creation, report submission, source upload, evidence search, graph slice, weekly report, and copilot endpoints.
  - Include sample requests and responses.
  - _Requirements: R1, R2, R4, R8, R9, R13, R16_

- [ ] 21.4 Create design-to-task traceability note
  - Map each major task group to the related design sections.
  - Keep this file aligned with future `design.md` changes.
  - _Requirements: R19_

---

## 22. Recommended Build Order

1. Project foundation and mock UI.
2. BigQuery schema and seed data.
3. Consultant dashboard, knowledge formation, and graph mock screens.
4. Business-side URL report form.
5. Source persistence.
6. Gemini extraction worker.
7. BigQuery persistence for extracted knowledge.
8. Elasticsearch indexing and evidence search.
9. Rule-based discovery detection.
10. Weekly report generation.
11. Report Copilot.
12. Conversational voice intake.
13. BigQuery Graph integration.
14. Demo polish.

## 23. Minimal Demo Acceptance Checklist

The MVP demo is acceptable when all of the following are true:

- [ ] A consultant can create or select a client workspace.
- [ ] A business-side user can submit information through a URL form.
- [ ] A business-side user can provide information through conversational voice or simulated voice chat.
- [ ] The system stores source data and creates structured observations, entities, relationships, and hypotheses.
- [ ] Observed facts and hypotheses are displayed separately.
- [ ] The consultant can see knowledge accumulation status.
- [ ] The consultant can search source evidence through Elasticsearch.
- [ ] The consultant can view at least three graph perspectives.
- [ ] The system can generate a weekly Discovery Report.
- [ ] The consultant can ask Report Copilot a question and receive an answer grounded in facts, hypotheses, and evidence.
- [ ] The implementation does not use Spanner.

## 24. References

- Kiro Feature Specs: https://kiro.dev/docs/specs/feature-specs/
- BigQuery Graph overview: https://cloud.google.com/bigquery/docs/graph-overview
- Elasticsearch hybrid search: https://www.elastic.co/elasticsearch/hybrid-search
- Gemini structured output: https://ai.google.dev/gemini-api/docs/structured-output
- Tailwind responsive design: https://tailwindcss.com/docs/responsive-design
- Next.js App Router: https://nextjs.org/docs/app
