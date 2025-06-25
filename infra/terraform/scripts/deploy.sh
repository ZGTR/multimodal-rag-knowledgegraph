#!/bin/bash

# Multimodal RAG Knowledge Graph - Terraform Deployment Script
# This script handles secure deployment across different environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    local env=$1
    print_status "Checking prerequisites..."
    
    # Check if Terraform is installed
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform is not installed. Please install it first."
        exit 1
    fi
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Skip AWS credentials check for local environment
    if [ "$env" != "local" ]; then
        # Check if AWS credentials are configured
        if ! aws sts get-caller-identity &> /dev/null; then
            print_error "AWS credentials not configured. Please run 'aws configure' first."
            exit 1
        fi
    fi
    
    print_success "Prerequisites check passed"
}

# Function to validate environment
validate_environment() {
    local env=$1
    
    case $env in
        "local"|"dev"|"staging"|"prod")
            return 0
            ;;
        *)
            print_error "Invalid environment: $env. Must be one of: local, dev, staging, prod"
            exit 1
            ;;
    esac
}

# Function to setup local environment
setup_local() {
    print_status "Setting up local environment..."
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    # Start local services
    print_status "Starting local PostgreSQL with pgvector..."
    docker-compose -f infra/local-dev/postgres/docker-compose.yml up -d
    
    print_status "Starting local Gremlin Server..."
    docker run -d --name gremlin-server -p 8182:8182 tinkerpop/gremlin-server:latest
    
    print_success "Local environment setup complete"
    print_status "You can now run the application locally with:"
    echo "  python -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo "  uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000"
}

# Function to get sensitive variables
get_sensitive_variables() {
    local env=$1
    
    print_status "Getting sensitive variables for environment: $env"
    
    # For production, use AWS Secrets Manager
    if [ "$env" = "prod" ]; then
        print_status "Using AWS Secrets Manager for production secrets..."
        
        # Get secrets from AWS Secrets Manager
        NEPTUNE_PASSWORD=$(aws secretsmanager get-secret-value --secret-id "/multimodal-rag-kg/prod/neptune-password" --query 'SecretString' --output text 2>/dev/null || echo "")
        POSTGRESQL_PASSWORD=$(aws secretsmanager get-secret-value --secret-id "/multimodal-rag-kg/prod/postgresql-password" --query 'SecretString' --output text 2>/dev/null || echo "")
        OPENAI_API_KEY=$(aws secretsmanager get-secret-value --secret-id "/multimodal-rag-kg/prod/openai-api-key" --query 'SecretString' --output text 2>/dev/null || echo "")
        
        if [ -z "$NEPTUNE_PASSWORD" ] || [ -z "$POSTGRESQL_PASSWORD" ]; then
            print_error "Required secrets not found in AWS Secrets Manager. Please create them first."
            exit 1
        fi
    else
        # For non-production, prompt for secrets
        print_warning "For non-production environments, you'll be prompted for sensitive values"
        read -s -p "Enter Neptune master password: " NEPTUNE_PASSWORD
        echo
        read -s -p "Enter PostgreSQL password: " POSTGRESQL_PASSWORD
        echo
        read -s -p "Enter OpenAI API key (optional): " OPENAI_API_KEY
        echo
    fi
    
    # Export variables for Terraform
    export TF_VAR_neptune_master_password="$NEPTUNE_PASSWORD"
    export TF_VAR_postgresql_password="$POSTGRESQL_PASSWORD"
    export TF_VAR_openai_api_key="$OPENAI_API_KEY"
}

# Function to deploy infrastructure
deploy_infrastructure() {
    local env=$1
    local action=$2
    
    print_status "Deploying infrastructure for environment: $env"
    
    # Change to Terraform directory
    cd infra/terraform
    
    # Initialize Terraform
    print_status "Initializing Terraform..."
    terraform init
    
    # Plan or apply based on action
    if [ "$action" = "plan" ]; then
        print_status "Creating Terraform plan..."
        terraform plan -var-file="environments/${env}.tfvars" -out=tfplan
        print_success "Plan created successfully. Review tfplan file."
    elif [ "$action" = "apply" ]; then
        print_status "Applying Terraform configuration..."
        terraform apply -var-file="environments/${env}.tfvars" -auto-approve
        print_success "Infrastructure deployed successfully!"
        
        # Show outputs
        print_status "Infrastructure outputs:"
        terraform output
    elif [ "$action" = "destroy" ]; then
        print_warning "This will destroy all infrastructure for environment: $env"
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            terraform destroy -var-file="environments/${env}.tfvars" -auto-approve
            print_success "Infrastructure destroyed successfully!"
        else
            print_status "Destroy cancelled"
        fi
    fi
    
    cd ../..
}

# Function to show usage
show_usage() {
    echo "Usage: $0 <environment> <action>"
    echo ""
    echo "Environments:"
    echo "  local     - Setup local development environment"
    echo "  dev       - Deploy to development environment"
    echo "  staging   - Deploy to staging environment"
    echo "  prod      - Deploy to production environment"
    echo ""
    echo "Actions:"
    echo "  setup     - Setup local environment (Docker services)"
    echo "  plan      - Create Terraform plan"
    echo "  apply     - Deploy infrastructure"
    echo "  destroy   - Destroy infrastructure"
    echo "  status    - Show infrastructure status"
    echo ""
    echo "Examples:"
    echo "  $0 local setup     # Setup local development environment"
    echo "  $0 dev plan        # Plan dev infrastructure"
    echo "  $0 dev apply       # Deploy dev infrastructure"
    echo "  $0 prod apply      # Deploy production infrastructure"
    echo "  $0 dev destroy     # Destroy dev infrastructure"
}

# Main script
main() {
    local environment=$1
    local action=$2
    
    # Check if arguments are provided
    if [ -z "$environment" ] || [ -z "$action" ]; then
        show_usage
        exit 1
    fi
    
    # Validate environment
    validate_environment "$environment"
    
    # Check prerequisites
    check_prerequisites "$environment"
    
    # Handle different actions
    case $action in
        "setup")
            if [ "$environment" = "local" ]; then
                setup_local
            else
                print_error "Setup action is only available for local environment"
                exit 1
            fi
            ;;
        "plan"|"apply"|"destroy")
            if [ "$environment" = "local" ]; then
                print_error "Terraform actions are not available for local environment"
                exit 1
            fi
            get_sensitive_variables "$environment"
            deploy_infrastructure "$environment" "$action"
            ;;
        "status")
            if [ "$environment" = "local" ]; then
                print_status "Local environment status:"
                docker ps --filter "name=gremlin-server|postgres"
            else
                cd infra/terraform
                terraform show
                cd ../..
            fi
            ;;
        *)
            print_error "Invalid action: $action"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@" 