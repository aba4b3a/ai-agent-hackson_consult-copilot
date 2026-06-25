CREATE TABLE IF NOT EXISTS `{TENANT_DATASET}.kpi_candidates` (
  kpi_candidate_id STRING NOT NULL,
  company_id STRING NOT NULL,
  common_kpi_id STRING,
  kpi_name STRING NOT NULL,
  kpi_domain STRING,
  kpi_type STRING,
  description STRING,
  calculation_hint STRING,
  data_source_hint STRING,
  measurement_frequency STRING,
  reason STRING,
  source_answer_event_ids ARRAY<STRING>,
  source_followup_answer_event_ids ARRAY<STRING>,
  source_gcs_uris ARRAY<STRING>,
  confidence FLOAT64,
  importance_score FLOAT64,
  approval_status STRING,
  approved_by STRING,
  approved_at TIMESTAMP,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP
)
CLUSTER BY company_id, kpi_domain, approval_status;

CREATE TABLE IF NOT EXISTS `{TENANT_DATASET}.focus_metric_candidates` (
  focus_metric_candidate_id STRING NOT NULL,
  company_id STRING NOT NULL,
  metric_name STRING NOT NULL,
  metric_category STRING,
  description STRING,
  related_kpi_candidate_ids ARRAY<STRING>,
  related_common_kpi_ids ARRAY<STRING>,
  observation_signal_types ARRAY<STRING>,
  calculation_hint STRING,
  data_source_hint STRING,
  measurement_frequency STRING,
  trigger_condition STRING,
  followup_policy STRING,
  reason STRING,
  source_answer_event_ids ARRAY<STRING>,
  source_followup_answer_event_ids ARRAY<STRING>,
  source_gcs_uris ARRAY<STRING>,
  confidence FLOAT64,
  priority_score FLOAT64,
  approval_status STRING,
  approved_by STRING,
  approved_at TIMESTAMP,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP
)
CLUSTER BY company_id, metric_category, approval_status;

CREATE TABLE IF NOT EXISTS `{TENANT_DATASET}.current_kpi_definitions` (
  kpi_id STRING NOT NULL,
  company_id STRING NOT NULL,
  common_kpi_id STRING,
  kpi_name STRING NOT NULL,
  kpi_domain STRING,
  kpi_type STRING,
  description STRING,
  calculation_formula STRING,
  unit STRING,
  measurement_frequency STRING,
  data_source_type STRING,
  data_source_detail STRING,
  status STRING,
  source_kpi_candidate_id STRING,
  source_wiki_uri STRING,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP
)
CLUSTER BY company_id, status, kpi_domain;

CREATE TABLE IF NOT EXISTS `{TENANT_DATASET}.current_focus_metric_definitions` (
  focus_metric_id STRING NOT NULL,
  company_id STRING NOT NULL,
  metric_name STRING NOT NULL,
  metric_category STRING,
  description STRING,
  related_kpi_ids ARRAY<STRING>,
  related_common_kpi_ids ARRAY<STRING>,
  observation_signal_types ARRAY<STRING>,
  calculation_method STRING,
  unit STRING,
  measurement_frequency STRING,
  trigger_condition STRING,
  followup_policy STRING,
  status STRING,
  source_focus_metric_candidate_id STRING,
  source_wiki_uri STRING,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP
)
CLUSTER BY company_id, status, metric_category;
