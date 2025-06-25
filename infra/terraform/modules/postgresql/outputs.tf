output "endpoint" {
  description = "PostgreSQL endpoint"
  value       = aws_db_instance.main.endpoint
}

output "port" {
  description = "PostgreSQL port"
  value       = aws_db_instance.main.port
}

output "database_name" {
  description = "Database name"
  value       = aws_db_instance.main.db_name
}

output "security_group_id" {
  description = "PostgreSQL security group ID"
  value       = aws_security_group.postgresql.id
} 