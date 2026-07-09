variable "project_id" {
  type = string
}

variable "services" {
  type = list(string)
  default = [
    "run.googleapis.com",
    "compute.googleapis.com",
    "artifactregistry.googleapis.com",
    "aiplatform.googleapis.com",
    "secretmanager.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "storage.googleapis.com",
    "bigquery.googleapis.com",
    "sts.googleapis.com",
  ]
}
