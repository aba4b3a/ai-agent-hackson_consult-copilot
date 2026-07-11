resource "google_storage_bucket" "artifacts" {
  name                        = "${var.project_id}-${var.service_prefix}-artifacts"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = false

  lifecycle_rule {
    condition {
      age = 14
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    project = var.service_prefix
    layer   = "artifacts"
  }
}

# LLM Wiki bucket: per-project, versioning enabled.
# Layout (matches agent/tools/storage_tools.py):
#   tenants/{company_id}/wiki/current/*
#   tenants/{company_id}/wiki/versions/<ts>/*
#   tenants/{company_id}/raw/fiscal_year=<n>/answers/*
#   tenants/{company_id}/derived/fiscal_year=<n>/*
resource "google_storage_bucket" "llm_wiki" {
  name                        = "${var.project_id}-${var.service_prefix}-wiki"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = false

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age                   = 90
      with_state            = "ARCHIVED"
      matches_storage_class = ["STANDARD"]
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  lifecycle_rule {
    condition {
      age        = 365
      with_state = "ARCHIVED"
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    project = var.service_prefix
    layer   = "wiki"
  }
}
