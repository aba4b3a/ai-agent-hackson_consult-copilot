variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "service_prefix" {
  type = string
}

variable "cloud_run_service_name" {
  type        = string
  description = "The Cloud Run v2 service name that the ALB should route to."
}
