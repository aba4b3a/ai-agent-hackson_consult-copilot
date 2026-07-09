# Single Cloud Run v2 service running three containers side-by-side:
#   - nginx  (ingress, port 8080): serves front static assets, reverse-proxies
#            /api/* -> localhost:8000 (back), /agent/* -> localhost:8081 (agent)
#   - back   (FastAPI, port 8000, sidecar)
#   - agent  (ADK api_server, port 8081, sidecar)
#
# Ingress is restricted to internal + LB. Terraform sets the initial image
# tags; subsequent redeploys happen out-of-band from GitHub Actions, and
# the lifecycle rule below prevents `terraform apply` from reverting them.

resource "google_cloud_run_v2_service" "app" {
  name     = "${var.service_prefix}-app"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  template {
    service_account = var.runtime_sa_email

    scaling {
      min_instance_count = var.min_instance_count
      max_instance_count = var.max_instance_count
    }

    # --- ingress: nginx (serves front + reverse-proxies to sidecars) ---
    containers {
      name  = "nginx"
      image = var.image_nginx

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      # Wait until back+agent are up before considering the instance ready.
      startup_probe {
        tcp_socket {
          port = 8080
        }
        initial_delay_seconds = 2
        timeout_seconds       = 3
        period_seconds        = 5
        failure_threshold     = 20
      }
    }

    # --- sidecar: FastAPI back on 8000 ---
    containers {
      name  = "back"
      image = var.image_back
      # Override the Dockerfile CMD to drop --reload (dev-only) in production.
      args = ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

      env {
        name  = "APP_ENV"
        value = "production"
      }
      env {
        name  = "DEBUG"
        value = "false"
      }
      env {
        name  = "DRY_RUN"
        value = "false"
      }
      env {
        name  = "GCP_PROJECT"
        value = var.project_id
      }
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "LOCATION"
        value = var.location
      }
      env {
        name  = "BQ_DATASET_PREFIX"
        value = var.bq_dataset_prefix
      }
      env {
        name  = "WIKI_BUCKET"
        value = var.wiki_bucket
      }
      env {
        name  = "AGENT_BASE_URL"
        value = "http://127.0.0.1:8081"
      }
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "MODEL_ID"
        value = var.model_id
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }

      startup_probe {
        tcp_socket {
          port = 8000
        }
        initial_delay_seconds = 2
        timeout_seconds       = 3
        period_seconds        = 5
        failure_threshold     = 20
      }
    }

    # --- sidecar: ADK agent on 8081 (overridden from default 8080) ---
    containers {
      name  = "agent"
      image = var.image_agent
      args  = ["adk", "api_server", "--host", "0.0.0.0", "--port", "8081", "agents"]

      env {
        name  = "APP_ENV"
        value = "production"
      }
      env {
        name  = "DRY_RUN"
        value = "false"
      }
      env {
        name  = "GCP_PROJECT"
        value = var.project_id
      }
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "LOCATION"
        value = var.location
      }
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = var.location
      }
      env {
        name  = "GOOGLE_GENAI_USE_VERTEXAI"
        value = "TRUE"
      }
      env {
        name  = "MODEL_ID"
        value = var.model_id
      }
      env {
        name  = "BQ_DATASET_PREFIX"
        value = var.bq_dataset_prefix
      }
      env {
        name  = "WIKI_BUCKET"
        value = var.wiki_bucket
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }

      startup_probe {
        tcp_socket {
          port = 8081
        }
        initial_delay_seconds = 2
        timeout_seconds       = 3
        period_seconds        = 5
        failure_threshold     = 20
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  # CI/CD updates image tags out-of-band. Terraform must not roll them back.
  lifecycle {
    ignore_changes = [
      client,
      client_version,
      template[0].containers[0].image,
      template[0].containers[1].image,
      template[0].containers[2].image,
    ]
  }
}

# Serverless NEG for the ALB needs run.invoker on the service. Because ingress
# is set to INTERNAL_LOAD_BALANCER, only traffic that arrives via the ALB
# reaches the service — this member alone does not expose *.run.app.
resource "google_cloud_run_v2_service_iam_member" "public_via_alb" {
  name     = google_cloud_run_v2_service.app.name
  location = google_cloud_run_v2_service.app.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}
