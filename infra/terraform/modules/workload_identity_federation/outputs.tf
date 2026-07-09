output "workload_identity_provider" {
  # Value used as workload_identity_provider in google-github-actions/auth.
  value = "projects/${data.google_project.current.number}/locations/global/workloadIdentityPools/${google_iam_workload_identity_pool.gha.workload_identity_pool_id}/providers/${google_iam_workload_identity_pool_provider.github.workload_identity_pool_provider_id}"
}

output "deploy_sa_email" {
  value = var.deploy_sa_email
}
