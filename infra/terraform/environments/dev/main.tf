locals {
  service_prefix = var.service_prefix
}

module "project_services" {
  source     = "../../modules/project_services"
  project_id = var.project_id
}

module "artifact_registry" {
  source         = "../../modules/artifact_registry"
  service_prefix = local.service_prefix
  region         = var.region

  depends_on = [module.project_services]
}

module "secret_manager" {
  source         = "../../modules/secret_manager"
  service_prefix = local.service_prefix

  depends_on = [module.project_services]
}

module "storage" {
  source         = "../../modules/storage"
  project_id     = var.project_id
  region         = var.region
  service_prefix = local.service_prefix

  depends_on = [module.project_services]
}

module "iam" {
  source                   = "../../modules/iam"
  project_id               = var.project_id
  service_prefix           = local.service_prefix
  bq_dataset_prefix        = var.bq_dataset_prefix
  wiki_bucket              = module.storage.wiki_bucket
  artifacts_bucket         = module.storage.artifacts_bucket
  gemini_api_key_secret_id = module.secret_manager.gemini_api_key_secret_id

  depends_on = [module.project_services]
}

module "workload_identity_federation" {
  source            = "../../modules/workload_identity_federation"
  project_id        = var.project_id
  service_prefix    = local.service_prefix
  github_repository = var.github_repository
  deploy_sa_name    = module.iam.deploy_sa_name
  deploy_sa_email   = module.iam.deploy_sa_email

  depends_on = [module.project_services]
}

module "cloud_run" {
  source            = "../../modules/cloud_run"
  project_id        = var.project_id
  region            = var.region
  service_prefix    = local.service_prefix
  runtime_sa_email  = module.iam.runtime_sa_email
  image_nginx       = var.image_nginx
  image_back        = var.image_back
  image_agent       = var.image_agent
  bq_dataset_prefix = var.bq_dataset_prefix
  wiki_bucket       = module.storage.wiki_bucket
  location          = var.region
  model_id          = var.model_id

  depends_on = [module.project_services, module.iam]
}

module "alb_http" {
  source                 = "../../modules/alb_http"
  project_id             = var.project_id
  region                 = var.region
  service_prefix         = local.service_prefix
  cloud_run_service_name = module.cloud_run.service_name

  depends_on = [module.project_services]
}
