variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs"
  type        = list(string)
}

variable "neptune_cluster_name" {
  description = "Neptune cluster name"
  type        = string
}

variable "neptune_instance_class" {
  description = "Neptune instance class"
  type        = string
}

variable "neptune_engine_version" {
  description = "Neptune engine version"
  type        = string
}

variable "neptune_backup_retention" {
  description = "Neptune backup retention period in days"
  type        = number
}

variable "kms_key_arn" {
  description = "KMS key ARN for encryption"
  type        = string
  default     = null
} 