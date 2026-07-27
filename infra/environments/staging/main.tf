module "platform" {
  source       = "../../modules/aws"
  cluster_name = "agent-foundry-staging"
  vpc_id       = var.vpc_id
  private_subnet_ids = var.private_subnet_ids
  db_username  = var.db_username
  db_password  = var.db_password
}
