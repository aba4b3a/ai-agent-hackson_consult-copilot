resource "google_service_account" "runtime" {
  account_id   = "ai-qualityops-runtime"
  display_name = "AI QualityOps runtime service account"
}
