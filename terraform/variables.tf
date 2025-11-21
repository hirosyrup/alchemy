variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "asia-northeast1"
}

variable "service_name" {
  description = "The Cloud Run service name"
  type        = string
  default     = "boat-race-worker"
}
