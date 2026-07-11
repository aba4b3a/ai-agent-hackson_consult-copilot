variable "project_id" {
  type = string
}

variable "service_prefix" {
  type = string
}

variable "github_repository" {
  type        = string
  description = "GitHub repo in owner/repo form (e.g. my-org/consult-copilot)."
}

variable "deploy_sa_name" {
  type        = string
  description = "Full resource name of the deploy SA (projects/.../serviceAccounts/...)."
}

variable "deploy_sa_email" {
  type        = string
  description = "Email of the deploy SA."
}
