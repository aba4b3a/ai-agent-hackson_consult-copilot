CREATE SCHEMA IF NOT EXISTS `local-project.cd_tenant_SMB_2198`
OPTIONS(location="asia-northeast1");

CREATE TABLE IF NOT EXISTS `local-project.cd_tenant_SMB_2198.onboarding_answer_events` (
  answer_event_id STRING NOT NULL,
  company_id STRING NOT NULL,
  question_id STRING NOT NULL,
  question_version STRING NOT NULL,
  question_text STRING,
  respondent_role STRING,
  answered_at TIMESTAMP NOT NULL,
  answer_text STRING,
  answer_payload JSON,
  extracted_summary STRING,
  extracted_entities JSON,
  extracted_signals JSON,
  source_gcs_uri STRING,
  source_file_generation STRING,
  created_at TIMESTAMP NOT NULL
)
PARTITION BY DATE(answered_at)
CLUSTER BY company_id, question_id;

CREATE TABLE IF NOT EXISTS `local-project.cd_tenant_SMB_2198.followup_answer_events` (
  followup_answer_event_id STRING NOT NULL,
  company_id STRING NOT NULL,
  research_task_id STRING,
  respondent_role STRING,
  answered_at TIMESTAMP NOT NULL,
  answer_text STRING,
  answer_payload JSON,
  extracted_summary STRING,
  extracted_signals JSON,
  created_at TIMESTAMP NOT NULL
)
PARTITION BY DATE(answered_at)
CLUSTER BY company_id, research_task_id;

CREATE TABLE IF NOT EXISTS `local-project.cd_tenant_SMB_2198.kpi_candidates` (
  kpi_candidate_id STRING NOT NULL,
  company_id STRING NOT NULL,
  kpi_name STRING NOT NULL,
  kpi_domain STRING,
  kpi_type STRING,
  description STRING,
  calculation_hint STRING,
  measurement_frequency STRING,
  data_source_hint STRING,
  approval_status STRING,
  confidence FLOAT64,
  source_answer_event_ids ARRAY<STRING>,
  source_followup_answer_event_ids ARRAY<STRING>,
  source_gcs_uris ARRAY<STRING>,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP
)
CLUSTER BY company_id, kpi_domain, approval_status;

CREATE TABLE IF NOT EXISTS `local-project.cd_tenant_SMB_2198.focus_metric_candidates` (
  focus_metric_candidate_id STRING NOT NULL,
  company_id STRING NOT NULL,
  metric_name STRING NOT NULL,
  metric_category STRING,
  description STRING,
  related_kpi_candidate_ids ARRAY<STRING>,
  observation_signal_types ARRAY<STRING>,
  trigger_condition STRING,
  followup_policy STRING,
  measurement_frequency STRING,
  approval_status STRING,
  confidence FLOAT64,
  source_answer_event_ids ARRAY<STRING>,
  source_followup_answer_event_ids ARRAY<STRING>,
  source_gcs_uris ARRAY<STRING>,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP
)
CLUSTER BY company_id, metric_category, approval_status;

CREATE OR REPLACE PROPERTY GRAPH `local-project.cd_tenant_SMB_2198.KnowledgeGraph`
NODE TABLES (
  `local-project.cd_tenant_SMB_2198.knowledge_nodes`
    KEY (node_id)
    LABEL KnowledgeNode
    PROPERTIES (company_id, node_type, label, description, confidence, status, properties)
)
EDGE TABLES (
  `local-project.cd_tenant_SMB_2198.knowledge_edges`
    SOURCE KEY (source_node_id) REFERENCES knowledge_nodes (node_id)
    DESTINATION KEY (target_node_id) REFERENCES knowledge_nodes (node_id)
    LABEL KnowledgeEdge
    PROPERTIES (company_id, edge_type, description, confidence, strength, observed_count, properties)
);
