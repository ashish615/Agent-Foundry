terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# GKE cluster
resource "google_container_cluster" "gke" {
  name     = var.cluster_name
  location = var.region

  remove_default_node_pool = true
  initial_node_count       = 1

  min_master_version = var.kubernetes_version
}

resource "google_container_node_pool" "primary" {
  name    = "primary"
  cluster = google_container_cluster.gke.name
  location = var.region

  node_count = var.node_count

  node_config {
    machine_type = var.machine_type
    oauth_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }
}

# Cloud SQL PostgreSQL
resource "google_sql_database_instance" "postgres" {
  name             = "${var.cluster_name}-postgres"
  database_version = "POSTGRES_16"
  region           = var.region

  settings {
    tier = var.db_tier
  }
}

# Memorystore Redis
resource "google_redis_instance" "redis" {
  name           = "${var.cluster_name}-redis"
  memory_size_gb = 1
  region         = var.region
}
