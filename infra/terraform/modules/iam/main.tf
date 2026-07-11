# Runtime SA — attached to the Cloud Run service. Least-privilege access to
# BigQuery / GCS / Vertex AI / Secret Manager.
resource "google_service_account" "runtime" {
  account_id   = "${var.service_prefix}-runtime"
  display_name = "${var.service_prefix} Cloud Run runtime"
}

# Deploy SA — impersonated by GitHub Actions via WIF to build/push images and
# deploy the Cloud Run service. Terraform grants roles/iam.serviceAccountUser
# so the deploy SA can "act as" the runtime SA when redeploying.
resource "google_service_account" "deploy" {
  account_id   = "${var.service_prefix}-deploy"
  display_name = "${var.service_prefix} GitHub Actions deployer"
}

# ---- Runtime SA role bindings ----

# BigQuery: dataset-scoped where possible. jobUser is project-scoped because
# BQ jobs are billed at the project level.
resource "google_bigquery_dataset_iam_member" "runtime_bq_editor" {
  project    = var.project_id
  dataset_id = var.bq_dataset_prefix
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_project_iam_member" "runtime_bq_jobuser" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.runtime.email}"
}

# Multiple services issue `CREATE SCHEMA IF NOT EXISTS ...` at startup — even
# when the dataset already exists, BigQuery still requires
# bigquery.datasets.create on the project to run that DDL. The narrower
# jobUser role above does not grant it. bigquery.user does, and also lets the
# app manage tenant-scoped datasets it creates itself. Data access on
# other-owned datasets is still gated by dataset-level grants (dataEditor
# above), so this stays inside the least-privilege envelope for our use case.
resource "google_project_iam_member" "runtime_bq_user" {
  project = var.project_id
  role    = "roles/bigquery.user"
  member  = "serviceAccount:${google_service_account.runtime.email}"
}

# GCS: object-level access on the two app buckets only.
resource "google_storage_bucket_iam_member" "runtime_wiki_admin" {
  bucket = var.wiki_bucket
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_storage_bucket_iam_member" "runtime_artifacts_admin" {
  bucket = var.artifacts_bucket
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.runtime.email}"
}

# Vertex AI (Gemini via Vertex, aka "Gemini Enterprise" model access).
resource "google_project_iam_member" "runtime_aiplatform_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.runtime.email}"
}

# Secret Manager: single specific secret only.
resource "google_secret_manager_secret_iam_member" "runtime_gemini_key" {
  secret_id = var.gemini_api_key_secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.runtime.email}"
}

# Observability.
resource "google_project_iam_member" "runtime_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_project_iam_member" "runtime_metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.runtime.email}"
}

# ---- Deploy SA role bindings ----

resource "google_project_iam_member" "deploy_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.deploy.email}"
}

resource "google_project_iam_member" "deploy_ar_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.deploy.email}"
}

# Required so `gcloud run deploy` can set the runtime SA on the service.
resource "google_service_account_iam_member" "deploy_act_as_runtime" {
  service_account_id = google_service_account.runtime.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.deploy.email}"
}
