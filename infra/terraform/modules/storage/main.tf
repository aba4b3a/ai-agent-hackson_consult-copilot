resource "google_storage_bucket" "artifacts" {
  name                        = "${var.project_id}-qualityops-artifacts"
  location                    = var.region
  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 14
    }

    action {
      type = "Delete"
    }
  }
}
