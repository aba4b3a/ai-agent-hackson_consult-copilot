resource "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "${var.service_prefix}-gemini-api-key"

  replication {
    auto {}
  }
}
