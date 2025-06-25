#!/bin/bash

# Local Development Setup Script
# This script helps set up environment variables for local development

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Function to check AWS CLI
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Please run 'aws configure' first."
        exit 1
    fi
}

# Function to get secrets from AWS Secrets Manager
get_secrets_from_aws() {
    local environment=$1
    
    print_status "Fetching secrets from AWS Secrets Manager for environment: $environment"
    
    # Get secrets from AWS Secrets Manager
    NEPTUNE_PASSWORD=$(aws secretsmanager get-secret-value --secret-id "/multimodal-rag-kg/$environment/neptune-password" --query 'SecretString' --output text 2>/dev/null || echo "")
    POSTGRESQL_PASSWORD=$(aws secretsmanager get-secret-value --secret-id "/multimodal-rag-kg/$environment/postgresql-password" --query 'SecretString' --output text 2>/dev/null || echo "")
    OPENAI_API_KEY=$(aws secretsmanager get-secret-value --secret-id "/multimodal-rag-kg/$environment/openai-api-key" --query 'SecretString' --output text 2>/dev/null || echo "")
    
    if [ -z "$NEPTUNE_PASSWORD" ] || [ -z "$POSTGRESQL_PASSWORD" ]; then
        print_warning "Some secrets not found in AWS Secrets Manager. You'll be prompted for them."
        return 1
    fi
    
    return 0
}

# Function to check for existing .env file
check_existing_env() {
    if [ -f ".env" ]; then
        print_status "Found existing .env file"
        
        # Check if required variables are present
        if grep -q "OPENAI_API_KEY=" .env && grep -q "NEPTUNE_PASSWORD=" .env && grep -q "POSTGRESQL_PASSWORD=" .env; then
            print_success "All required environment variables found in .env file"
            return 0
        else
            print_warning "Some required environment variables missing from .env file"
            return 1
        fi
    fi
    return 1
}

# Function to load existing .env file
load_existing_env() {
    print_status "Loading environment variables from existing .env file"
    
    # Source the .env file to load variables
    export $(grep -v '^#' .env | xargs)
    
    # Verify the variables are loaded
    if [ -n "$OPENAI_API_KEY" ] && [ -n "$NEPTUNE_PASSWORD" ] && [ -n "$POSTGRESQL_PASSWORD" ]; then
        print_success "Environment variables loaded successfully"
        return 0
    else
        print_warning "Some environment variables are empty or missing"
        return 1
    fi
}

# Function to prompt for secrets
prompt_for_secrets() {
    print_status "Please provide the required secrets for local development:"
    
    read -s -p "Enter Neptune password: " NEPTUNE_PASSWORD
    echo
    read -s -p "Enter PostgreSQL password: " POSTGRESQL_PASSWORD
    echo
    read -s -p "Enter OpenAI API key (optional, press Enter to skip): " OPENAI_API_KEY
    echo
}

# Function to create .env file
create_env_file() {
    local environment=$1
    
    print_status "Creating .env file for local development..."
    
    cat > .env << EOF
# Local Development Environment Variables
# Generated from AWS Secrets Manager for environment: $environment

# Database Passwords
NEPTUNE_PASSWORD=$NEPTUNE_PASSWORD
POSTGRESQL_PASSWORD=$POSTGRESQL_PASSWORD

# API Keys
OPENAI_API_KEY=$OPENAI_API_KEY

# Application Configuration
APP_ENV=local
LOG_LEVEL=debug
EMBEDDING_MODEL_NAME=text-embedding-3-small

# Local Database Connections
VECTORDB_URI=postgresql://postgres:$POSTGRESQL_PASSWORD@localhost:5432/vectordb
KG_URI=ws://localhost:8182/gremlin
EOF

    print_success ".env file created successfully!"
    print_warning "Remember to add .env to your .gitignore file if it's not already there."
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [environment]"
    echo ""
    echo "This script sets up environment variables for local development."
    echo ""
    echo "Arguments:"
    echo "  environment  - AWS environment to fetch secrets from (dev, staging, prod)"
    echo "                 If not provided, will check for existing .env file or prompt for secrets"
    echo ""
    echo "Examples:"
    echo "  $0 dev        # Fetch secrets from AWS Secrets Manager for dev environment"
    echo "  $0            # Use existing .env file or prompt for secrets manually"
    echo ""
    echo "Note: If a .env file already exists with all required variables, it will be used."
    echo "      Otherwise, you'll be prompted to create one."
}

# Main script
main() {
    local environment=$1
    
    # First, check if we have an existing .env file
    if check_existing_env; then
        if load_existing_env; then
            print_success "Using existing .env file for local development"
            exit 0
        fi
    fi
    
    # Check if AWS CLI is available and configured
    if command -v aws &> /dev/null && aws sts get-caller-identity &> /dev/null; then
        if [ -n "$environment" ]; then
            print_status "Using AWS Secrets Manager for environment: $environment"
            if get_secrets_from_aws "$environment"; then
                create_env_file "$environment"
                exit 0
            fi
        fi
    fi
    
    # Fall back to manual input
    print_status "Using manual input for secrets"
    prompt_for_secrets
    create_env_file "manual"
}

# Run main function with all arguments
main "$@" 