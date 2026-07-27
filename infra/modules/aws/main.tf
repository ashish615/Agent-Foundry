terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# EKS cluster
module "eks" {
  source          = "terraform-aws-modules/eks/aws"
  version         = "~> 20.0"
  cluster_name    = var.cluster_name
  cluster_version = var.kubernetes_version
  vpc_id          = var.vpc_id
  subnet_ids      = var.private_subnet_ids
}

# RDS PostgreSQL
resource "aws_db_instance" "postgres" {
  identifier        = "${var.cluster_name}-postgres"
  engine            = "postgres"
  engine_version    = "16"
  instance_class    = var.db_instance_class
  allocated_storage = 20
  db_name           = "agent_foundry"
  username          = var.db_username
  password          = var.db_password
  skip_final_snapshot = true
}

# ElastiCache Redis
resource "aws_elasticache_cluster" "redis" {
  cluster_id      = "${var.cluster_name}-redis"
  engine          = "redis"
  node_type       = var.redis_node_type
  num_cache_nodes = 1
  port            = 6379
}

# S3 bucket for model weights and audit logs
resource "aws_s3_bucket" "storage" {
  bucket = "${var.cluster_name}-storage"
}
