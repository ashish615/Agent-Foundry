terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

# AKS cluster
resource "azurerm_kubernetes_cluster" "aks" {
  name                = var.cluster_name
  location            = var.location
  resource_group_name = var.resource_group_name
  dns_prefix          = var.cluster_name
  kubernetes_version  = var.kubernetes_version

  default_node_pool {
    name       = "system"
    node_count = var.node_count
    vm_size    = var.vm_size
  }

  identity {
    type = "SystemAssigned"
  }
}

# Azure DB for PostgreSQL
resource "azurerm_postgresql_flexible_server" "postgres" {
  name                   = "${var.cluster_name}-postgres"
  resource_group_name    = var.resource_group_name
  location               = var.location
  version                = "16"
  administrator_login    = var.db_username
  administrator_password = var.db_password
  sku_name               = "B_Standard_B1ms"
}

# Azure Cache for Redis
resource "azurerm_redis_cache" "redis" {
  name                = "${var.cluster_name}-redis"
  location            = var.location
  resource_group_name = var.resource_group_name
  capacity            = 1
  family              = "C"
  sku_name            = "Basic"
}
