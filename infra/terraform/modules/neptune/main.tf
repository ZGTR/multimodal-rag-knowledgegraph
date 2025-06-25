# Neptune Module
resource "aws_security_group" "neptune" {
  name_prefix = "${var.project_name}-${var.environment}-neptune-"
  vpc_id      = var.vpc_id

  # Allow Neptune port from within VPC
  ingress {
    from_port   = 8182
    to_port     = 8182
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  # Allow HTTPS for Neptune API
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-neptune-sg"
    Environment = var.environment
  }
}

# Neptune Subnet Group
resource "aws_neptune_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}-neptune-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name        = "${var.project_name}-${var.environment}-neptune-subnet-group"
    Environment = var.environment
  }
}

# Neptune Parameter Group
resource "aws_neptune_parameter_group" "main" {
  family = "neptune1.3"
  name   = "${var.project_name}-${var.environment}-neptune-params"

  parameter {
    name  = "neptune_enable_audit_log"
    value = "1"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-neptune-params"
    Environment = var.environment
  }
}

# Neptune Cluster
resource "aws_neptune_cluster" "main" {
  cluster_identifier                  = var.neptune_cluster_name
  engine                              = "neptune"
  engine_version                      = var.neptune_engine_version
  db_subnet_group_name                = aws_neptune_subnet_group.main.name
  db_cluster_parameter_group_name     = aws_neptune_parameter_group.main.name
  vpc_security_group_ids              = [aws_security_group.neptune.id]
  backup_retention_period             = var.neptune_backup_retention
  preferred_backup_window             = "03:00-04:00"
  preferred_maintenance_window        = "sun:04:00-sun:05:00"
  skip_final_snapshot                 = var.environment != "prod"
  deletion_protection                 = var.environment == "prod"
  storage_encrypted                   = true
  kms_key_arn                         = var.kms_key_arn

  tags = {
    Name        = "${var.project_name}-${var.environment}-neptune-cluster"
    Environment = var.environment
  }
}

# Neptune Instance
resource "aws_neptune_cluster_instance" "main" {
  identifier         = "${var.neptune_cluster_name}-instance"
  cluster_identifier = aws_neptune_cluster.main.id
  engine             = "neptune"
  instance_class     = var.neptune_instance_class

  tags = {
    Name        = "${var.project_name}-${var.environment}-neptune-instance"
    Environment = var.environment
  }
} 