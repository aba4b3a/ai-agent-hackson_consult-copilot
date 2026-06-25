CREATE TABLE IF NOT EXISTS `{TENANT_DATASET}.onboarding_answer_events` (
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

CREATE TABLE IF NOT EXISTS `{TENANT_DATASET}.research_followup_question_events` (
  followup_question_id STRING NOT NULL,
  company_id STRING NOT NULL,
  generated_at TIMESTAMP NOT NULL,
  question_text STRING NOT NULL,
  question_category STRING,
  target_role STRING,
  reason STRING,
  related_kpi_candidates ARRAY<STRING>,
  related_focus_metric_candidates ARRAY<STRING>,
  expected_answer_format STRING,
  priority_score FLOAT64,
  status STRING,
  source_answer_event_ids ARRAY<STRING>,
  source_gcs_uri STRING,
  created_at TIMESTAMP NOT NULL
)
PARTITION BY DATE(generated_at)
CLUSTER BY company_id, status, question_category;

CREATE TABLE IF NOT EXISTS `{TENANT_DATASET}.followup_answer_events` (
  followup_answer_event_id STRING NOT NULL,
  company_id STRING NOT NULL,
  followup_question_id STRING NOT NULL,
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
CLUSTER BY company_id, followup_question_id;
