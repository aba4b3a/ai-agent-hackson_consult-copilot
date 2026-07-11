data "google_project" "current" {
  project_id = var.project_id
}

# Workload Identity Pool for GitHub Actions.
resource "google_iam_workload_identity_pool" "gha" {
  workload_identity_pool_id = "${var.service_prefix}-gha"
  display_name              = "${var.service_prefix} GitHub Actions"
  description               = "Federates GitHub Actions OIDC tokens to the deploy SA."
}

# OIDC provider inside the pool. Restricts token exchange to a single repo.
resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.gha.workload_identity_pool_id
  workload_identity_pool_provider_id = "github"
  display_name                       = "GitHub OIDC"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
    "attribute.ref"        = "assertion.ref"
    "attribute.actor"      = "assertion.actor"
  }

  attribute_condition = "assertion.repository == \"${var.github_repository}\""

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# Allow only workflows in this repo to impersonate the deploy SA.
resource "google_service_account_iam_member" "deploy_wif_binding" {
  service_account_id = var.deploy_sa_name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/projects/${data.google_project.current.number}/locations/global/workloadIdentityPools/${google_iam_workload_identity_pool.gha.workload_identity_pool_id}/attribute.repository/${var.github_repository}"
}
