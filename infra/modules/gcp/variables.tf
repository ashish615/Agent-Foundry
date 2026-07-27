variable "cluster_name" {
  type = string
}

variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "kubernetes_version" {
  type    = string
  default = "1.30"
}

variable "node_count" {
  type    = number
  default = 3
}

variable "machine_type" {
  type    = string
  default = "n2-standard-4"
}

variable "db_tier" {
  type    = string
  default = "db-f1-micro"
}
