output "service_name" {
  value = google_cloud_run_v2_service.app.name
}

output "service_location" {
  value = google_cloud_run_v2_service.app.location
}

output "service_uri" {
  # *.run.app URL. Ingress is restricted so this returns 403 unless traffic
  # arrives via the ALB; kept as an output for debugging.
  value = google_cloud_run_v2_service.app.uri
}
