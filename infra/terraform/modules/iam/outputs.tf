output "runtime_sa_email" {
  value = google_service_account.runtime.email
}

output "runtime_sa_name" {
  # full resource name — needed for WIF binding
  value = google_service_account.runtime.name
}

output "deploy_sa_email" {
  value = google_service_account.deploy.email
}

output "deploy_sa_name" {
  value = google_service_account.deploy.name
}
