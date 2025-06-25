#!/bin/bash

# Setup AWS Secrets Manager for Multimodal RAG Knowledge Graph
# This script helps create and manage secrets for different environments

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

# Function to create secret
create_secret() {
    local secret_name=$1
    local secret_value=$2
    local description=$3
    
    print_status "Creating secret: $secret_name"
    
    # Check if secret already exists
    if aws secretsmanager describe-secret --secret-id "$secret_name" &> /dev/null; then
        print_warning "Secret $secret_name already exists. Updating..."
        aws secretsmanager update-secret --secret-id "$secret_name" --secret-string "$secret_value"
    else
        aws secretsmanager create-secret \
            --name "$secret_name" \
            --description "$description" \
            --secret-string "$secret_value"
    fi
    
    print_success "Secret $secret_name created/updated successfully"
}

# Function to setup environment secrets
setup_environment_secrets() {
    local environment=$1
    
    print_status "Setting up secrets for environment: $environment"
    
    # Get secrets from user input
    echo
    read -s -p "Enter Neptune master password: " neptune_password
    echo
    read -s -p "Enter PostgreSQL password: " postgresql_password
    echo
    read -s -p "Enter OpenAI API key (optional, press Enter to skip): " openai_api_key
    echo
    
    # Create secrets
    create_secret \
        "/multimodal-rag-kg/$environment/neptune-password" \
        "$neptune_password" \
        "Neptune master password for $environment environment"
    
    create_secret \
        "/multimodal-rag-kg/$environment/postgresql-password" \
        "$postgresql_password" \
        "PostgreSQL password for $environment environment"
    
    if [ -n "$openai_api_key" ]; then
        create_secret \
            "/multimodal-rag-kg/$environment/openai-api-key" \
            "$openai_api_key" \
            "OpenAI API key for $environment environment"
    fi
}

# Function to list secrets
list_secrets() {
    local environment=$1
    
    print_status "Listing secrets for environment: $environment"
    
    aws secretsmanager list-secrets \
        --filters Key=name,Values="/multimodal-rag-kg/$environment/" \
        --query 'SecretList[*].[Name,Description,LastModifiedDate]' \
        --output table
}

# Function to delete secrets
delete_secrets() {
    local environment=$1
    
    print_warning "This will delete all secrets for environment: $environment"
    read -p "Are you sure? (yes/no): " confirm
    
    if [ "$confirm" = "yes" ]; then
        print_status "Deleting secrets for environment: $environment"
        
        # List secrets to delete
        secrets=$(aws secretsmanager list-secrets \
            --filters Key=name,Values="/multimodal-rag-kg/$environment/" \
            --query 'SecretList[*].Name' \
            --output text)
        
        for secret in $secrets; do
            print_status "Deleting secret: $secret"
            aws secretsmanager delete-secret --secret-id "$secret" --force-delete-without-recovery
        done
        
        print_success "All secrets for $environment deleted successfully"
    else
        print_status "Deletion cancelled"
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 <action> [environment]"
    echo ""
    echo "Actions:"
    echo "  setup <env>    - Setup secrets for environment (dev/staging/prod)"
    echo "  list <env>     - List secrets for environment"
    echo "  delete <env>   - Delete all secrets for environment"
    echo "  rotate <env>   - Rotate secrets for environment"
    echo ""
    echo "Examples:"
    echo "  $0 setup prod     # Setup production secrets"
    echo "  $0 setup staging  # Setup staging secrets"
    echo "  $0 list prod      # List production secrets"
    echo "  $0 delete dev     # Delete development secrets"
}

# Function to rotate secrets
rotate_secrets() {
    local environment=$1
    
    print_status "Rotating secrets for environment: $environment"
    
    # Generate new passwords
    neptune_password=$(openssl rand -base64 32)
    postgresql_password=$(openssl rand -base64 32)
    
    # Update secrets
    create_secret \
        "/multimodal-rag-kg/$environment/neptune-password" \
        "$neptune_password" \
        "Neptune master password for $environment environment (rotated)"
    
    create_secret \
        "/multimodal-rag-kg/$environment/postgresql-password" \
        "$postgresql_password" \
        "PostgreSQL password for $environment environment (rotated)"
    
    print_success "Secrets rotated successfully"
    print_warning "You will need to update your application configuration with the new passwords"
}

# Main script
main() {
    local action=$1
    local environment=$2
    
    # Check AWS CLI
    check_aws_cli
    
    # Check if arguments are provided
    if [ -z "$action" ]; then
        show_usage
        exit 1
    fi
    
    # Handle different actions
    case $action in
        "setup")
            if [ -z "$environment" ]; then
                print_error "Environment is required for setup action"
                show_usage
                exit 1
            fi
            setup_environment_secrets "$environment"
            ;;
        "list")
            if [ -z "$environment" ]; then
                print_error "Environment is required for list action"
                show_usage
                exit 1
            fi
            list_secrets "$environment"
            ;;
        "delete")
            if [ -z "$environment" ]; then
                print_error "Environment is required for delete action"
                show_usage
                exit 1
            fi
            delete_secrets "$environment"
            ;;
        "rotate")
            if [ -z "$environment" ]; then
                print_error "Environment is required for rotate action"
                show_usage
                exit 1
            fi
            rotate_secrets "$environment"
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