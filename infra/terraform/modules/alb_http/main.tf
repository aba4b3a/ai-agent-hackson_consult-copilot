# External HTTP(S) Application Load Balancer fronting a single Cloud Run
# service via a Serverless NEG. HTTP-only for now; HTTPS can be layered on
# later without recreating the IP or backend.

resource "google_compute_global_address" "alb_ip" {
  name = "${var.service_prefix}-alb-ip"
}

resource "google_compute_region_network_endpoint_group" "cloud_run_neg" {
  name                  = "${var.service_prefix}-alb-neg"
  region                = var.region
  network_endpoint_type = "SERVERLESS"

  cloud_run {
    service = var.cloud_run_service_name
  }
}

resource "google_compute_backend_service" "default" {
  name                  = "${var.service_prefix}-alb-backend"
  protocol              = "HTTP"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  # Note: timeout_sec is NOT supported when the backend is a Serverless NEG
  # (Cloud Run / App Engine / Cloud Functions). GCP rejects the field with a
  # 400. Request-level timeouts are governed by the Cloud Run service itself.

  backend {
    group = google_compute_region_network_endpoint_group.cloud_run_neg.id
  }

  log_config {
    enable      = true
    sample_rate = 1.0
  }
}

resource "google_compute_url_map" "default" {
  name            = "${var.service_prefix}-alb-urlmap"
  default_service = google_compute_backend_service.default.id
}

resource "google_compute_target_http_proxy" "default" {
  name    = "${var.service_prefix}-alb-http-proxy"
  url_map = google_compute_url_map.default.id
}

resource "google_compute_global_forwarding_rule" "http" {
  name                  = "${var.service_prefix}-alb-fwd-http"
  target                = google_compute_target_http_proxy.default.id
  port_range            = "80"
  ip_address            = google_compute_global_address.alb_ip.address
  load_balancing_scheme = "EXTERNAL_MANAGED"
}
