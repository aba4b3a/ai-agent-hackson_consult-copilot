resource "google_cloud_run_v2_service" "back" {
  name     = "${local.service_prefix}-back"
  location = var.region

  template {
    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }

    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello"
    }
  }
}

resource "google_cloud_run_v2_service" "agent" {
  name     = "${local.service_prefix}-agent"
  location = var.region

  template {
    scaling {
      min_instance_count = 0
      max_instance_count = 1
    }

    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello"
    }
  }
}
