# Enable required APIs
resource "google_project_service" "services" {
  for_each = toset([
    "run.googleapis.com",
    "firestore.googleapis.com",
    "pubsub.googleapis.com",
    "cloudscheduler.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com"
  ])
  service            = each.key
  disable_on_destroy = false
}

# Artifact Registry Repository
resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = "alchemy-repo"
  description   = "Docker repository for Alchemy System"
  format        = "DOCKER"

  depends_on = [google_project_service.services]
}

# Firestore Database
resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_project_service.services]
}

# Pub/Sub Topic for Race Events
resource "google_pubsub_topic" "race_events" {
  name = "alchemy-events"
  depends_on = [google_project_service.services]
}

# Cloud Run Service (Worker)
# Note: Using a placeholder image initially. User needs to deploy the actual image.
resource "google_cloud_run_v2_service" "worker" {
  name     = var.service_name
  location = var.region
  ingress = "INGRESS_TRAFFIC_INTERNAL_ONLY" # Only triggered by Pub/Sub

  template {
    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello" # Placeholder
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
    }
  }
  depends_on = [google_project_service.services]
}

# Pub/Sub Subscription (Push to Cloud Run)
resource "google_pubsub_subscription" "worker_subscription" {
  name  = "race-events-sub"
  topic = google_pubsub_topic.race_events.name

  push_config {
    push_endpoint = "${google_cloud_run_v2_service.worker.uri}/pubsub/handler"
    oidc_token {
      service_account_email = google_service_account.invoker.email
    }
  }
}

# Service Account for Pub/Sub to invoke Cloud Run
resource "google_service_account" "invoker" {
  account_id   = "cloud-run-pubsub-invoker"
  display_name = "Cloud Run Pub/Sub Invoker"
}

resource "google_cloud_run_service_iam_binding" "invoker_binding" {
  location = google_cloud_run_v2_service.worker.location
  service  = google_cloud_run_v2_service.worker.name
  role     = "roles/run.invoker"
  members  = ["serviceAccount:${google_service_account.invoker.email}"]
}

# Cloud Scheduler (Dispatcher)
# Triggers every minute to check for upcoming races
resource "google_cloud_scheduler_job" "dispatcher" {
  name             = "alchemy-dispatcher"
  description      = "Triggers the dispatcher every minute"
  schedule         = "* * * * *"
  time_zone        = "Asia/Tokyo"
  attempt_deadline = "320s"

  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_v2_service.worker.uri}/dispatch" # Assuming dispatcher is also in the worker app
    oidc_token {
      service_account_email = google_service_account.invoker.email
    }
  }
  depends_on = [google_project_service.services]
}
