# General variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "multimodal-rag-kg"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# VPC variables
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "private_subnets" {
  description = "Private subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "public_subnets" {
  description = "Public subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24"]
}

# Neptune variables
variable "neptune_cluster_name" {
  description = "Neptune cluster name"
  type        = string
  default     = "multimodal-rag-kg"
}

variable "neptune_instance_class" {
  description = "Neptune instance class"
  type        = string
  default     = "db.r5.large"
}

variable "neptune_engine_version" {
  description = "Neptune engine version"
  type        = string
  default     = "1.3.1.0"
}

variable "neptune_backup_retention" {
  description = "Neptune backup retention period in days"
  type        = number
  default     = 7
}

variable "neptune_master_username" {
  description = "Neptune master username"
  type        = string
  default     = "admin"
}

variable "neptune_master_password" {
  description = "Neptune master password"
  type        = string
  sensitive   = true
}

# PostgreSQL variables
variable "postgresql_db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "vectordb"
}

variable "postgresql_username" {
  description = "PostgreSQL username"
  type        = string
  default     = "postgres"
}

variable "postgresql_password" {
  description = "PostgreSQL password"
  type        = string
  sensitive   = true
}

variable "postgresql_instance_class" {
  description = "PostgreSQL instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "postgresql_allocated_storage" {
  description = "PostgreSQL allocated storage in GB"
  type        = number
  default     = 20
}

variable "postgresql_engine_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "14.10"
}

# Application variables
variable "app_image" {
  description = "Docker image for the application"
  type        = string
  default     = "multimodal-rag-kg:latest"
}

variable "app_port" {
  description = "Application port"
  type        = number
  default     = 8000
}

variable "app_cpu" {
  description = "Application CPU units"
  type        = number
  default     = 256
}

variable "app_memory" {
  description = "Application memory in MiB"
  type        = number
  default     = 512
}

variable "embedding_model_name" {
  description = "Embedding model name"
  type        = string
  default     = "text-embedding-3-small"
}

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
  default     = ""
} 