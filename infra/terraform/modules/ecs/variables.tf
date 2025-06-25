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

variable "private_subnet_ids" {
  description = "Private subnet IDs"
  type        = list(string)
}

variable "alb_target_group_arn" {
  description = "ALB target group ARN"
  type        = string
}

variable "alb_security_group_id" {
  description = "ALB security group ID"
  type        = string
}

variable "app_image" {
  description = "Docker image for the application"
  type        = string
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

variable "app_desired_count" {
  description = "Desired number of application instances"
  type        = number
  default     = 2
}

variable "app_environment_variables" {
  description = "Environment variables for the application"
  type        = map(string)
  default     = {}
}

variable "app_secrets" {
  description = "Secrets for the application (from AWS Secrets Manager)"
  type        = map(string)
  default     = {}
} 