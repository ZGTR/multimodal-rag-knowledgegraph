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

variable "public_subnet_ids" {
  description = "Public subnet IDs"
  type        = list(string)
}

variable "app_port" {
  description = "Application port"
  type        = number
  default     = 8000
}

variable "certificate_arn" {
  description = "SSL certificate ARN"
  type        = string
  default     = null
} 