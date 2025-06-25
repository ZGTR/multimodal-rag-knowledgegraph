output "cluster_endpoint" {
  description = "Neptune cluster endpoint"
  value       = aws_neptune_cluster.main.endpoint
}

output "cluster_arn" {
  description = "Neptune cluster ARN"
  value       = aws_neptune_cluster.main.arn
}

output "cluster_id" {
  description = "Neptune cluster ID"
  value       = aws_neptune_cluster.main.cluster_identifier
}

output "security_group_id" {
  description = "Neptune security group ID"
  value       = aws_security_group.neptune.id
} 