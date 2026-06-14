resource "google_artifact_registry_repository" "containers" {
  location      = var.region
  repository_id = "consult-copilot"
  description   = "AI QualityOps container images"
  format        = "DOCKER"
}
