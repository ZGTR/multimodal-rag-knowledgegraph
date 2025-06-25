# PostgreSQL Module
resource "aws_security_group" "postgresql" {
  name_prefix = "${var.project_name}-${var.environment}-postgresql-"
  vpc_id      = var.vpc_id

  # Allow PostgreSQL port from within VPC
  ingress {
    from_port   = 5432
    to_port     = 5432
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
    Name        = "${var.project_name}-${var.environment}-postgresql-sg"
    Environment = var.environment
  }
}

# DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}-postgresql-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name        = "${var.project_name}-${var.environment}-postgresql-subnet-group"
    Environment = var.environment
  }
}

# Parameter Group for pgvector
resource "aws_db_parameter_group" "main" {
  family = "postgres14"
  name   = "${var.project_name}-${var.environment}-postgresql-params"

  parameter {
    name  = "shared_preload_libraries"
    value = "vector"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-postgresql-params"
    Environment = var.environment
  }
}

# PostgreSQL Instance
resource "aws_db_instance" "main" {
  identifier = "${var.project_name}-${var.environment}-postgresql"

  engine         = "postgres"
  engine_version = var.engine_version
  instance_class = var.instance_class

  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_type          = "gp2"
  storage_encrypted     = true

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.postgresql.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  parameter_group_name   = aws_db_parameter_group.main.name

  backup_retention_period = var.backup_retention_period
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  skip_final_snapshot = var.environment != "prod"
  deletion_protection = var.environment == "prod"

  # Performance Insights
  performance_insights_enabled = var.environment == "prod"
  performance_insights_retention_period = var.environment == "prod" ? 7 : 0

  # Monitoring
  monitoring_interval = var.environment == "prod" ? 60 : 0
  monitoring_role_arn = var.monitoring_role_arn

  tags = {
    Name        = "${var.project_name}-${var.environment}-postgresql"
    Environment = var.environment
  }
}

# Lambda function to enable pgvector extension
resource "aws_lambda_function" "enable_pgvector" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "${var.project_name}-${var.environment}-enable-pgvector"
  role            = aws_iam_role.lambda_role.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 300

  environment {
    variables = {
      DB_HOST     = aws_db_instance.main.endpoint
      DB_NAME     = var.db_name
      DB_USERNAME = var.db_username
      DB_PASSWORD = var.db_password
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-enable-pgvector"
    Environment = var.environment
  }
}

# Lambda execution role
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-${var.environment}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Lambda basic execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda function code
data "archive_file" "lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/lambda_function.zip"

  source {
    content = <<EOF
import psycopg2
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    try:
        conn = psycopg2.connect(
            host=os.environ['DB_HOST'],
            database=os.environ['DB_NAME'],
            user=os.environ['DB_USERNAME'],
            password=os.environ['DB_PASSWORD']
        )
        
        with conn.cursor() as cur:
            # Enable pgvector extension
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            conn.commit()
            
        conn.close()
        logger.info("pgvector extension enabled successfully")
        return {"statusCode": 200, "body": "pgvector extension enabled"}
        
    except Exception as e:
        logger.error(f"Error enabling pgvector: {str(e)}")
        raise e
EOF
    filename = "index.py"
  }
}

# Invoke Lambda after RDS is ready
resource "null_resource" "enable_pgvector" {
  depends_on = [aws_db_instance.main, aws_lambda_function.enable_pgvector]

  provisioner "local-exec" {
    command = "aws lambda invoke --function-name ${aws_lambda_function.enable_pgvector.function_name} --region ${data.aws_region.current.name} response.json"
  }
} 