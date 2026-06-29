# Research dispatch: Cloud Scheduler -> Pub/Sub -> Cloud Run subscriber.
#
# Architecture:
#   1. Cloud Scheduler fires a daily tick (default 09:00 JST). Operators can
#      add more schedules per tenant by adding google_cloud_scheduler_job blocks.
#   2. Each tick publishes to a single Pub/Sub topic (research_dispatch_tick).
#      The payload tells the worker which tenant cohort to scan.
#   3. The Cloud Run "back" service subscribes (push) to that topic and runs
#      research_dispatch_service.tick(...): for each company with active
#      research_followup_question_events in status=proposed, the service
#      materializes per-target-role assignments into Firestore (handled in
#      back/app/services/research_service.py).
#
# Why a single topic rather than a topic per tenant:
# - Tenants are added at runtime; provisioning a topic per tenant from
#   Terraform forces a Terraform write for every onboarding.
# - The cohort filter inside the worker handles fan-out, and is cheap
#   compared to per-tenant topic management.

resource "google_pubsub_topic" "research_dispatch_tick" {
  name = "consult-copilot-research-dispatch-tick"

  labels = {
    project = "consult-copilot"
    layer   = "research"
  }

  message_retention_duration = "86400s"
}

resource "google_pubsub_topic" "research_question_assigned" {
  name = "consult-copilot-research-question-assigned"

  labels = {
    project = "consult-copilot"
    layer   = "research"
  }

  message_retention_duration = "604800s"
}

# Daily tick at 09:00 JST. Adjust via terraform variables if needed.
resource "google_cloud_scheduler_job" "research_dispatch_daily" {
  name      = "consult-copilot-research-dispatch-daily"
  schedule  = "0 9 * * *"
  time_zone = "Asia/Tokyo"
  region    = var.region

  pubsub_target {
    topic_name = google_pubsub_topic.research_dispatch_tick.id
    data       = base64encode(jsonencode({ cohort = "all", reason = "daily-tick" }))
  }
}

# Weekly tick on Monday at 09:00 JST — Research Agent default cadence per
# the design ("ask sales weekly").
resource "google_cloud_scheduler_job" "research_dispatch_weekly" {
  name      = "consult-copilot-research-dispatch-weekly"
  schedule  = "0 9 * * 1"
  time_zone = "Asia/Tokyo"
  region    = var.region

  pubsub_target {
    topic_name = google_pubsub_topic.research_dispatch_tick.id
    data       = base64encode(jsonencode({ cohort = "weekly", reason = "weekly-tick" }))
  }
}
