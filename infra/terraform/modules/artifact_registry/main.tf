resource "google_artifact_registry_repository" "containers" {
  location      = var.region
  repository_id = var.service_prefix
  description   = "${var.service_prefix} container images"
  format        = "DOCKER"
}
