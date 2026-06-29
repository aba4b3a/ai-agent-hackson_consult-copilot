locals {
  common_dataset_id = "cd_common"
}

resource "google_bigquery_dataset" "common" {
  dataset_id  = local.common_dataset_id
  location    = var.region
  description = "Consult Copilot common dataset (companies, masters, dataset registry, migration history)"

  default_table_expiration_ms = null
  delete_contents_on_destroy  = false

  labels = {
    project = "consult-copilot"
    layer   = "common"
  }
}

resource "google_bigquery_table" "companies" {
  dataset_id          = google_bigquery_dataset.common.dataset_id
  table_id            = "companies"
  description         = "Company directory. One row per tenant."
  deletion_protection = false

  clustering = ["company_id", "industry_code", "company_size_segment"]

  schema = jsonencode([
    { name = "company_id", type = "STRING", mode = "REQUIRED" },
    { name = "company_name", type = "STRING", mode = "REQUIRED" },
    { name = "legal_name", type = "STRING", mode = "NULLABLE" },
    { name = "industry_code", type = "STRING", mode = "NULLABLE" },
    { name = "industry_name", type = "STRING", mode = "NULLABLE" },
    { name = "sub_industry_code", type = "STRING", mode = "NULLABLE" },
    { name = "sub_industry_name", type = "STRING", mode = "NULLABLE" },
    { name = "business_type", type = "STRING", mode = "NULLABLE" },
    { name = "company_size_segment", type = "STRING", mode = "NULLABLE" },
    { name = "employee_count", type = "INT64", mode = "NULLABLE" },
    { name = "annual_revenue_range", type = "STRING", mode = "NULLABLE" },
    { name = "region_country", type = "STRING", mode = "NULLABLE" },
    { name = "region_prefecture", type = "STRING", mode = "NULLABLE" },
    { name = "region_city", type = "STRING", mode = "NULLABLE" },
    { name = "primary_sales_channels", type = "STRING", mode = "REPEATED" },
    { name = "primary_customer_types", type = "STRING", mode = "REPEATED" },
    { name = "primary_revenue_models", type = "STRING", mode = "REPEATED" },
    { name = "onboarding_status", type = "STRING", mode = "NULLABLE" },
    { name = "active_status", type = "STRING", mode = "NULLABLE" },
    { name = "created_at", type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "updated_at", type = "TIMESTAMP", mode = "NULLABLE" },
  ])
}

resource "google_bigquery_table" "company_dataset_registry" {
  dataset_id          = google_bigquery_dataset.common.dataset_id
  table_id            = "company_dataset_registry"
  description         = "Mapping of company_id to its BigQuery tenant dataset."
  deletion_protection = false

  clustering = ["company_id", "dataset_status"]

  schema = jsonencode([
    { name = "company_id", type = "STRING", mode = "REQUIRED" },
    { name = "dataset_project_id", type = "STRING", mode = "REQUIRED" },
    { name = "dataset_id", type = "STRING", mode = "REQUIRED" },
    { name = "dataset_region", type = "STRING", mode = "REQUIRED" },
    { name = "schema_version", type = "STRING", mode = "NULLABLE" },
    { name = "dataset_status", type = "STRING", mode = "NULLABLE" },
    { name = "created_at", type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "updated_at", type = "TIMESTAMP", mode = "NULLABLE" },
  ])
}

resource "google_bigquery_table" "onboarding_question_master" {
  dataset_id          = google_bigquery_dataset.common.dataset_id
  table_id            = "onboarding_question_master"
  description         = "Versioned master of the common initial 18 onboarding questions."
  deletion_protection = false

  clustering = ["version", "question_category"]

  schema = jsonencode([
    { name = "question_id", type = "STRING", mode = "REQUIRED" },
    { name = "version", type = "STRING", mode = "REQUIRED" },
    { name = "question_order", type = "INT64", mode = "REQUIRED" },
    { name = "question_text", type = "STRING", mode = "REQUIRED" },
    { name = "question_category", type = "STRING", mode = "REQUIRED" },
    { name = "answer_type", type = "STRING", mode = "REQUIRED" },
    { name = "purpose", type = "STRING", mode = "NULLABLE" },
    { name = "related_kpi_domains", type = "STRING", mode = "REPEATED" },
    { name = "related_focus_metric_categories", type = "STRING", mode = "REPEATED" },
    { name = "is_required", type = "BOOL", mode = "REQUIRED" },
    { name = "is_active", type = "BOOL", mode = "REQUIRED" },
    { name = "created_at", type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "updated_at", type = "TIMESTAMP", mode = "NULLABLE" },
  ])
}

resource "google_bigquery_table" "common_kpi_master" {
  dataset_id          = google_bigquery_dataset.common.dataset_id
  table_id            = "common_kpi_master"
  description         = "Common KPI templates referenced by per-tenant kpi_candidates."
  deletion_protection = false

  clustering = ["kpi_domain", "kpi_type"]

  schema = jsonencode([
    { name = "common_kpi_id", type = "STRING", mode = "REQUIRED" },
    { name = "kpi_name", type = "STRING", mode = "REQUIRED" },
    { name = "kpi_domain", type = "STRING", mode = "REQUIRED" },
    { name = "kpi_type", type = "STRING", mode = "NULLABLE" },
    { name = "description", type = "STRING", mode = "NULLABLE" },
    { name = "standard_calculation_formula", type = "STRING", mode = "NULLABLE" },
    { name = "standard_unit", type = "STRING", mode = "NULLABLE" },
    { name = "recommended_frequency", type = "STRING", mode = "NULLABLE" },
    { name = "applicable_industry_codes", type = "STRING", mode = "REPEATED" },
    { name = "applicable_business_types", type = "STRING", mode = "REPEATED" },
    { name = "is_active", type = "BOOL", mode = "REQUIRED" },
    { name = "created_at", type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "updated_at", type = "TIMESTAMP", mode = "NULLABLE" },
  ])
}

resource "google_bigquery_table" "schema_migration_history" {
  dataset_id          = google_bigquery_dataset.common.dataset_id
  table_id            = "schema_migration_history"
  description         = "Append-only log of DDL migrations applied to common or tenant datasets."
  deletion_protection = false

  clustering = ["target_scope", "target_dataset", "version"]

  schema = jsonencode([
    { name = "migration_id", type = "STRING", mode = "REQUIRED" },
    { name = "target_scope", type = "STRING", mode = "REQUIRED" },
    { name = "target_dataset", type = "STRING", mode = "REQUIRED" },
    { name = "version", type = "STRING", mode = "REQUIRED" },
    { name = "migration_name", type = "STRING", mode = "REQUIRED" },
    { name = "checksum", type = "STRING", mode = "REQUIRED" },
    { name = "applied_at", type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "applied_by", type = "STRING", mode = "NULLABLE" },
    { name = "status", type = "STRING", mode = "NULLABLE" },
    { name = "error_message", type = "STRING", mode = "NULLABLE" },
  ])
}
