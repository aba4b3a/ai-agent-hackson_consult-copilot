variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "service_prefix" {
  type = string
}

variable "runtime_sa_email" {
  type = string
}

# Container images. Managed by CI/CD; Terraform-provided values here are only
# the initial bootstrap tags. The Cloud Run service ignores subsequent image
# drift so `gcloud run deploy` from GitHub Actions can update tags without
# Terraform fighting it back (see lifecycle in main.tf).
variable "image_nginx" {
  type        = string
  description = "Full image ref for the nginx ingress container (baked with front static)."
}

variable "image_back" {
  type        = string
  description = "Full image ref for the FastAPI back container."
}

variable "image_agent" {
  type        = string
  description = "Full image ref for the ADK agent container."
}

variable "bq_dataset_prefix" {
  type = string
}

variable "wiki_bucket" {
  type = string
}

variable "location" {
  type        = string
  description = "Vertex AI / app LOCATION env var (usually the same as region)."
}

variable "model_id" {
  type    = string
  default = "gemini-2.5-flash"
}

variable "min_instance_count" {
  type    = number
  default = 0
}

variable "max_instance_count" {
  type    = number
  default = 2
}
