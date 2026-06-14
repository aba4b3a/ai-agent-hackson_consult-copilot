resource "google_service_account" "runtime" {
  account_id   = "consult-copilot-runtime"
  display_name = "AI QualityOps runtime service account"
}
