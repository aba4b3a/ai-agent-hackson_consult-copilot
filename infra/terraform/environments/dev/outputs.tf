output "alb_ip_address" {
  value = module.alb_http.alb_ip_address
}

output "cloud_run_service_name" {
  value = module.cloud_run.service_name
}

output "cloud_run_service_uri" {
  value = module.cloud_run.service_uri
}

output "artifact_registry_repository" {
  value = module.artifact_registry.repository_id
}

output "artifact_registry_url" {
  value = module.artifact_registry.repository_url
}

output "runtime_sa_email" {
  value = module.iam.runtime_sa_email
}

output "deploy_sa_email" {
  value = module.iam.deploy_sa_email
}

output "workload_identity_provider" {
  value = module.workload_identity_federation.workload_identity_provider
}

output "wiki_bucket" {
  value = module.storage.wiki_bucket
}
