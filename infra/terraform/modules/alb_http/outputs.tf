output "alb_ip_address" {
  value = google_compute_global_address.alb_ip.address
}

output "backend_service_id" {
  value = google_compute_backend_service.default.id
}

output "url_map_id" {
  value = google_compute_url_map.default.id
}
