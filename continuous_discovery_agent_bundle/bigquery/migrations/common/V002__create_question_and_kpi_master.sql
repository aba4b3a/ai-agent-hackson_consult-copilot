CREATE TABLE IF NOT EXISTS `cd_common.onboarding_question_master` (
  question_id STRING NOT NULL,
  version STRING NOT NULL,
  question_order INT64 NOT NULL,
  question_text STRING NOT NULL,
  question_category STRING NOT NULL,
  answer_type STRING NOT NULL,
  purpose STRING,
  related_kpi_domains ARRAY<STRING>,
  related_focus_metric_categories ARRAY<STRING>,
  is_required BOOL NOT NULL,
  is_active BOOL NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP
)
CLUSTER BY version, question_category;

CREATE TABLE IF NOT EXISTS `cd_common.common_kpi_master` (
  common_kpi_id STRING NOT NULL,
  kpi_name STRING NOT NULL,
  kpi_domain STRING NOT NULL,
  kpi_type STRING,
  description STRING,
  standard_calculation_formula STRING,
  standard_unit STRING,
  recommended_frequency STRING,
  applicable_industry_codes ARRAY<STRING>,
  applicable_business_types ARRAY<STRING>,
  is_active BOOL NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP
)
CLUSTER BY kpi_domain, kpi_type;
