output "repository_id" {
  value = google_artifact_registry_repository.containers.repository_id
}

output "repository_url" {
  # e.g. asia-northeast1-docker.pkg.dev/<project>/<repo>
  value = "${var.region}-docker.pkg.dev/${google_artifact_registry_repository.containers.project}/${google_artifact_registry_repository.containers.repository_id}"
}

output "repository_name" {
  # full resource name for IAM bindings
  value = google_artifact_registry_repository.containers.name
}
