# Deployment Guide: Multimodal RAG Knowledge Graph

This guide explains how to deploy the Multimodal RAG Knowledge Graph application across different environments (local, dev, staging, prod) while maintaining security best practices.

## 🏗️ Architecture Overview

The application uses a multi-database architecture:
- **Neptune**: Graph database for knowledge graph storage and relationships
- **PostgreSQL with pgvector**: Vector database for semantic search and embeddings
- **FastAPI**: RESTful API for ingestion and search operations
- **ECS Fargate**: Containerized application deployment
- **Application Load Balancer**: HTTPS termination and load balancing

## 🔐 Security Model

### Local Development
- Uses Docker containers for databases
- Secrets stored in `.env` files (not committed to git)
- No AWS resources required

### AWS Environments
- **Dev/Staging**: Secrets prompted during deployment
- **Production**: Secrets stored in AWS Secrets Manager
- All databases encrypted at rest and in transit
- Private subnets with NAT Gateway for internet access

## 🚀 Quick Start

### 1. Local Development Setup

```bash
# Clone and setup
git clone <repository-url>
cd multimodal-rag-knowledgegraph

# Setup local environment (Docker services)
./infra/terraform/scripts/deploy.sh local setup

# Install Python dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment variables
# Option 1: Fetch from AWS Secrets Manager (if you have AWS access)
./scripts/local-dev.sh dev

# Option 2: Create .env file manually
./scripts/local-dev.sh

# Start the application
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. AWS Environment Deployment

```bash
# Setup secrets for your environment
./infra/terraform/scripts/setup-secrets.sh setup dev

# Deploy to development environment
./infra/terraform/scripts/deploy.sh dev apply

# Deploy to production environment
./infra/terraform/scripts/deploy.sh prod apply
```

## 📋 Prerequisites

### Required Tools
- **Terraform** (>= 1.0)
- **AWS CLI** (configured with appropriate permissions)
- **Docker** (for local development)
- **Python** (3.11+)

### AWS Permissions
Your AWS user/role needs permissions for:
- VPC, EC2, ECS, RDS, Neptune
- IAM (for ECS roles)
- CloudWatch Logs
- Secrets Manager (for production)
- Application Load Balancer

## 🔧 Environment Configuration

### Environment-Specific Settings

| Environment | Neptune Instance | PostgreSQL Instance | Backup Retention | Monitoring |
|-------------|------------------|-------------------|------------------|------------|
| **Local** | Docker | Docker | N/A | None |
| **Dev** | db.r5.large | db.t3.micro | 1 day | Basic |
| **Staging** | db.r5.xlarge | db.t3.small | 3 days | Enhanced |
| **Prod** | db.r5.2xlarge | db.t3.medium | 7 days | Full |

### Configuration Files

```
infra/terraform/
├── environments/
│   ├── dev.tfvars      # Development settings
│   ├── staging.tfvars  # Staging settings
│   └── prod.tfvars     # Production settings
├── terraform.tfvars.example  # Template (copy to terraform.tfvars)
└── scripts/
    ├── deploy.sh       # Main deployment script
    └── setup-secrets.sh # Secrets management
```

## 🔒 Secrets Management

The project now uses AWS Secrets Manager for all sensitive configuration values, providing better security and consistency across environments.

### Local Development

For local development, you have two options:

#### Option 1: Use AWS Secrets Manager (Recommended)

If you have AWS access and secrets are already configured:

```bash
# Fetch secrets from AWS Secrets Manager for dev environment
./scripts/local-dev.sh dev
```

#### Option 2: Manual Configuration

If you don't have AWS access or want to use local values:

```bash
# Create .env file with manual input
./scripts/local-dev.sh
```

This will prompt you for:
- Neptune password
- PostgreSQL password  
- OpenAI API key (optional)

### AWS Environments

All AWS environments use AWS Secrets Manager with the following structure:
```
/multimodal-rag-kg/{environment}/{secret-name}
```

#### Required Secrets
- `/multimodal-rag-kg/{environment}/neptune-password`
- `/multimodal-rag-kg/{environment}/postgresql-password`
- `/multimodal-rag-kg/{environment}/openai-api-key`

#### Setting Up Secrets

```bash
# Setup secrets for an environment
./infra/terraform/scripts/setup-secrets.sh setup dev

# List secrets for an environment
./infra/terraform/scripts/setup-secrets.sh list dev

# Rotate secrets for an environment
./infra/terraform/scripts/setup-secrets.sh rotate dev
```

## 🚀 Deployment Workflows

### Development Workflow

1. **Local Development**
   ```bash
   # Setup local environment
   ./infra/terraform/scripts/deploy.sh local setup
   
   # Run application locally
   uvicorn src.api.main:app --reload
   ```

2. **Deploy to Dev**
   ```bash
   # Plan deployment
   ./infra/terraform/scripts/deploy.sh dev plan
   
   # Deploy (prompts for secrets)
   ./infra/terraform/scripts/deploy.sh dev apply
   ```

3. **Test and Iterate**
   ```bash
   # Check status
   ./infra/terraform/scripts/deploy.sh dev status
   
   # View logs
   aws logs tail /ecs/multimodal-rag-kg-dev --follow
   ```

### Production Deployment

1. **Setup Production Secrets**
   ```bash
   ./infra/terraform/scripts/setup-secrets.sh setup prod
   ```

2. **Deploy to Staging First**
   ```bash
   ./infra/terraform/scripts/deploy.sh staging apply
   # Test thoroughly in staging
   ```

3. **Deploy to Production**
   ```bash
   ./infra/terraform/scripts/deploy.sh prod apply
   ```

4. **Verify Deployment**
   ```bash
   # Check health
   curl https://your-alb-dns-name/health
   
   # Monitor logs
   aws logs tail /ecs/multimodal-rag-kg-prod --follow
   ```

## 🔍 Monitoring and Troubleshooting

### Health Checks

```bash
# Application health
curl https://your-alb-dns-name/health

# Neptune connectivity
aws neptune describe-db-clusters --db-cluster-identifier multimodal-rag-kg-prod

# PostgreSQL connectivity
aws rds describe-db-instances --db-instance-identifier multimodal-rag-kg-prod-postgresql
```

### Logs

```bash
# Application logs
aws logs tail /ecs/multimodal-rag-kg-{environment} --follow

# Neptune logs (via console)
# AWS Console > Neptune > Databases > Your Cluster > Logs

# PostgreSQL logs (via console)
# AWS Console > RDS > Databases > Your Instance > Logs
```

### Common Issues

1. **ECS Service Not Starting**
   - Check CloudWatch logs
   - Verify security group rules
   - Check task definition

2. **Database Connection Issues**
   - Verify security group rules
   - Check VPC connectivity
   - Verify credentials

3. **Terraform State Issues**
   ```bash
   # Force unlock if needed
   terraform force-unlock <lock-id>
   
   # Refresh state
   terraform refresh
   ```

## 💰 Cost Optimization

### Development
- Use smallest instance types
- Minimal backup retention
- Disable enhanced monitoring
- Destroy when not in use

### Production
- Right-size instances based on load
- Enable auto-scaling
- Use reserved instances for predictable workloads
- Monitor and optimize storage

### Cost Estimation (Monthly)
- **Dev**: ~$200-300/month
- **Staging**: ~$400-600/month
- **Prod**: ~$800-1200/month

## 🧹 Cleanup

### Destroy Infrastructure

```bash
# Destroy dev environment
./infra/terraform/scripts/deploy.sh dev destroy

# Destroy staging environment
./infra/terraform/scripts/deploy.sh staging destroy

# Destroy production environment
./infra/terraform/scripts/deploy.sh prod destroy
```

### Cleanup Local Environment

```bash
# Stop Docker services
docker-compose -f infra/postgres/docker-compose.yml down
docker stop gremlin-server
docker rm gremlin-server
```

### Cleanup Secrets

```bash
# Delete secrets for environment
./infra/terraform/scripts/setup-secrets.sh delete dev
./infra/terraform/scripts/setup-secrets.sh delete staging
./infra/terraform/scripts/setup-secrets.sh delete prod
```

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy to AWS

on:
  push:
    branches: [main, staging]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2
      
      - name: Deploy to staging
        if: github.ref == 'refs/heads/staging'
        run: |
          ./infra/terraform/scripts/deploy.sh staging apply
      
      - name: Deploy to production
        if: github.ref == 'refs/heads/main'
        run: |
          ./infra/terraform/scripts/deploy.sh prod apply
```

## 📚 Additional Resources

- [Terraform Documentation](https://www.terraform.io/docs)
- [AWS Neptune Documentation](https://docs.aws.amazon.com/neptune/)
- [AWS RDS Documentation](https://docs.aws.amazon.com/rds/)
- [ECS Documentation](https://docs.aws.amazon.com/ecs/)

## 🆘 Support

For issues or questions:
1. Check the troubleshooting section
2. Review CloudWatch logs
3. Check AWS service health
4. Review Terraform documentation
5. Check the project's GitHub issues

## 🔐 Security Checklist

- [ ] Never commit secrets to version control
- [ ] Use AWS Secrets Manager for production
- [ ] Enable encryption at rest and in transit
- [ ] Use least privilege IAM policies
- [ ] Regularly rotate credentials
- [ ] Monitor access logs and metrics
- [ ] Keep Terraform state secure
- [ ] Enable CloudTrail for audit logging
- [ ] Use VPC flow logs for network monitoring
- [ ] Implement proper backup and recovery procedures 