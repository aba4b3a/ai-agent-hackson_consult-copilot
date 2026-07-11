output "gemini_api_key_secret_id" {
  value = google_secret_manager_secret.gemini_api_key.secret_id
}

output "gemini_api_key_id" {
  value = google_secret_manager_secret.gemini_api_key.id
}
