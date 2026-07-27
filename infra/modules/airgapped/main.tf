# Air-gapped deployment: all images pulled from an internal Harbor registry.
# Extends the on-prem module; set airgapped = true in root values to activate.

module "onprem" {
  source         = "../onprem"
  namespace      = var.namespace
  db_password    = var.db_password
  minio_password = var.minio_password
}

# Harbor private container registry
resource "helm_release" "harbor" {
  name       = "harbor"
  repository = "https://helm.goharbor.io"
  chart      = "harbor"
  version    = "1.14.0"
  namespace  = var.namespace

  set {
    name  = "harborAdminPassword"
    value = var.harbor_admin_password
  }

  set {
    name  = "expose.type"
    value = "clusterIP"
  }
}
