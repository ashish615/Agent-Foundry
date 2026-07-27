variable "cluster_name" {
  type = string
}

variable "location" {
  type    = string
  default = "eastus"
}

variable "resource_group_name" {
  type = string
}

variable "kubernetes_version" {
  type    = string
  default = "1.30"
}

variable "node_count" {
  type    = number
  default = 3
}

variable "vm_size" {
  type    = string
  default = "Standard_D4s_v3"
}

variable "db_username" {
  type      = string
  sensitive = true
}

variable "db_password" {
  type      = string
  sensitive = true
}
