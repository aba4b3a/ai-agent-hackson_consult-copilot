variable "project_id" {
  type        = string
  description = "GCP project ID."
}

variable "region" {
  type        = string
  description = "GCP region."
  default     = "asia-northeast1"
}

variable "service_prefix" {
  type        = string
  description = "Common resource name prefix."
  default     = "consult-copilot"
}

variable "bq_dataset_prefix" {
  type        = string
  description = "BigQuery dataset the app reads/writes (must already exist)."
  default     = "consultant_copilot"
}

variable "github_repository" {
  type        = string
  description = "GitHub repo in owner/repo form for Workload Identity Federation."
}

variable "image_nginx" {
  type        = string
  description = "Full image ref for the nginx ingress. Placeholder is fine on first apply; CI overwrites it."
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "image_back" {
  type        = string
  description = "Full image ref for the back container. Placeholder is fine on first apply."
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "image_agent" {
  type        = string
  description = "Full image ref for the agent container. Placeholder is fine on first apply."
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "model_id" {
  type    = string
  default = "gemini-2.5-flash"
}
