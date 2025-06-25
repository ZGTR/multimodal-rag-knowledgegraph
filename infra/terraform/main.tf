terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    # Configure your S3 backend for state management
    # bucket = "your-terraform-state-bucket"
    # key    = "multimodal-rag-kg/terraform.tfstate"
    # region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
data "aws_secretsmanager_secret_version" "postgresql_password" {
  secret_id = "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:/multimodal-rag-kg/${var.environment}/postgresql-password"
}

# VPC and networking
module "vpc" {
  source = "./modules/vpc"
  
  project_name = var.project_name
  environment  = var.environment
  vpc_cidr     = var.vpc_cidr
  
  availability_zones = var.availability_zones
  private_subnets    = var.private_subnets
  public_subnets     = var.public_subnets
}

# Neptune Knowledge Graph
module "neptune" {
  source = "./modules/neptune"
  
  project_name = var.project_name
  environment  = var.environment
  
  vpc_id             = module.vpc.vpc_id
  vpc_cidr           = var.vpc_cidr
  private_subnet_ids = module.vpc.private_subnet_ids
  
  neptune_cluster_name     = var.neptune_cluster_name
  neptune_instance_class   = var.neptune_instance_class
  neptune_engine_version   = var.neptune_engine_version
  neptune_backup_retention = var.neptune_backup_retention
  
  depends_on = [module.vpc]
}

# PostgreSQL Vector Database
module "postgresql" {
  source = "./modules/postgresql"
  
  project_name = var.project_name
  environment  = var.environment
  
  vpc_id             = module.vpc.vpc_id
  vpc_cidr           = var.vpc_cidr
  private_subnet_ids = module.vpc.private_subnet_ids
  
  db_name           = var.postgresql_db_name
  db_username       = var.postgresql_username
  db_password       = data.aws_secretsmanager_secret_version.postgresql_password.secret_string
  instance_class    = var.postgresql_instance_class
  allocated_storage = var.postgresql_allocated_storage
  engine_version    = var.postgresql_engine_version
  
  depends_on = [module.vpc]
}

# Application Load Balancer (if needed for API)
module "alb" {
  source = "./modules/alb"
  
  project_name = var.project_name
  environment  = var.environment
  
  vpc_id             = module.vpc.vpc_id
  public_subnet_ids  = module.vpc.public_subnet_ids
  
  depends_on = [module.vpc]
}

# ECS Cluster and Service for the API
module "ecs" {
  source = "./modules/ecs"
  
  project_name = var.project_name
  environment  = var.environment
  
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  alb_target_group_arn = module.alb.target_group_arn
  
  # Database endpoints
  neptune_endpoint = module.neptune.cluster_endpoint
  postgresql_endpoint = module.postgresql.endpoint
  
  # Application configuration
  app_image = var.app_image
  app_port  = var.app_port
  app_cpu   = var.app_cpu
  app_memory = var.app_memory
  
  # Environment variables (non-sensitive)
  app_environment_variables = {
    NEPTUNE_CLUSTER_ENDPOINT = module.neptune.cluster_endpoint
    NEPTUNE_PORT             = "8182"
    NEPTUNE_REGION           = var.aws_region
    NEPTUNE_USE_SSL          = "true"
    NEPTUNE_VERIFY_SSL       = "true"
    VECTORDB_URI             = "postgresql://${var.postgresql_username}@${module.postgresql.endpoint}:5432/${var.postgresql_db_name}"
    EMBEDDING_MODEL_NAME     = var.embedding_model_name
    APP_ENV                  = var.environment
    LOG_LEVEL                = var.environment == "prod" ? "info" : "debug"
  }
  
  # Secrets from AWS Secrets Manager
  app_secrets = {
    NEPTUNE_PASSWORD = "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:/multimodal-rag-kg/${var.environment}/neptune-password"
    POSTGRESQL_PASSWORD = "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:/multimodal-rag-kg/${var.environment}/postgresql-password"
    OPENAI_API_KEY = "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:/multimodal-rag-kg/${var.environment}/openai-api-key"
  }
  
  depends_on = [module.neptune, module.postgresql, module.alb]
}

# Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "neptune_cluster_endpoint" {
  description = "Neptune cluster endpoint"
  value       = module.neptune.cluster_endpoint
  sensitive   = true
}

output "postgresql_endpoint" {
  description = "PostgreSQL endpoint"
  value       = module.postgresql.endpoint
  sensitive   = true
}

output "alb_dns_name" {
  description = "Application Load Balancer DNS name"
  value       = module.alb.dns_name
}

output "ecs_service_name" {
  description = "ECS service name"
  value       = module.ecs.service_name
}

output "api_url" {
  description = "API URL"
  value       = "http://${module.alb.dns_name}"
} 