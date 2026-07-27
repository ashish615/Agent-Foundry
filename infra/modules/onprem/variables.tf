variable "namespace" {
  type    = string
  default = "agent-foundry"
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "minio_password" {
  type      = string
  sensitive = true
}
