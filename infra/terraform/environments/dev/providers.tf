terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  # Remote state. The bucket must be created manually before the first
  # `terraform init` (see docs/deploy.md). Bucket name convention:
  #   <project_id>-<service_prefix>-tfstate
  backend "gcs" {
    # bucket is provided via `-backend-config=bucket=...` at init time so
    # project_id stays in tfvars, not in code.
    prefix = "dev"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
