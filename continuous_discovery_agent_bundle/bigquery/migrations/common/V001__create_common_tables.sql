CREATE TABLE IF NOT EXISTS `cd_common.companies` (
  company_id STRING NOT NULL,
  company_name STRING NOT NULL,
  legal_name STRING,
  industry_code STRING,
  industry_name STRING,
  sub_industry_code STRING,
  sub_industry_name STRING,
  business_type STRING,
  company_size_segment STRING,
  employee_count INT64,
  annual_revenue_range STRING,
  region_country STRING,
  region_prefecture STRING,
  region_city STRING,
  primary_sales_channels ARRAY<STRING>,
  primary_customer_types ARRAY<STRING>,
  primary_revenue_models ARRAY<STRING>,
  onboarding_status STRING,
  active_status STRING,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP
)
CLUSTER BY company_id, industry_code, company_size_segment;

CREATE TABLE IF NOT EXISTS `cd_common.company_dataset_registry` (
  company_id STRING NOT NULL,
  dataset_project_id STRING NOT NULL,
  dataset_id STRING NOT NULL,
  dataset_region STRING NOT NULL,
  schema_version STRING,
  dataset_status STRING,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP
)
CLUSTER BY company_id, dataset_status;

CREATE TABLE IF NOT EXISTS `cd_common.schema_migration_history` (
  migration_id STRING NOT NULL,
  target_scope STRING NOT NULL,
  target_dataset STRING NOT NULL,
  version STRING NOT NULL,
  migration_name STRING NOT NULL,
  checksum STRING NOT NULL,
  applied_at TIMESTAMP NOT NULL,
  applied_by STRING,
  status STRING,
  error_message STRING
)
CLUSTER BY target_scope, target_dataset, version;
