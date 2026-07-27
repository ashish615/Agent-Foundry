terraform {
  required_providers {
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
}

# Assumes an existing Kubernetes cluster; deploys PostgreSQL and Redis via Helm
resource "helm_release" "postgresql" {
  name       = "postgresql"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "postgresql"
  version    = "15.5.0"
  namespace  = var.namespace

  set {
    name  = "auth.postgresPassword"
    value = var.db_password
  }
}

resource "helm_release" "redis" {
  name       = "redis"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "redis"
  version    = "19.6.0"
  namespace  = var.namespace
}

resource "helm_release" "minio" {
  name       = "minio"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "minio"
  version    = "14.6.0"
  namespace  = var.namespace

  set {
    name  = "auth.rootPassword"
    value = var.minio_password
  }
}
