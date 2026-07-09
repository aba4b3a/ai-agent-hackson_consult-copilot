variable "project_id" {
  type = string
}

variable "service_prefix" {
  type = string
}

variable "bq_dataset_prefix" {
  type        = string
  description = "Name of the (already-existing) BigQuery dataset the app reads/writes."
}

variable "wiki_bucket" {
  type        = string
  description = "GCS bucket name for llm-wiki data."
}

variable "artifacts_bucket" {
  type        = string
  description = "GCS bucket name for artifacts."
}

variable "gemini_api_key_secret_id" {
  type        = string
  description = "Secret ID for the Gemini API key (Secret Manager)."
}
