output "artifacts_bucket" {
  value = google_storage_bucket.artifacts.name
}

output "wiki_bucket" {
  value = google_storage_bucket.llm_wiki.name
}
