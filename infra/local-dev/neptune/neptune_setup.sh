#!/bin/bash

# AWS Neptune Setup Script for Multimodal RAG Knowledge Graph
# This script helps you create and configure an AWS Neptune cluster

set -e

echo "🚀 AWS Neptune Setup for Multimodal RAG Knowledge Graph"
echo "======================================================"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first:"
    echo "   https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run:"
    echo "   aws configure"
    exit 1
fi

echo "✅ AWS CLI and credentials verified"

# Get user input
read -p "Enter your AWS region (default: us-east-1): " AWS_REGION
AWS_REGION=${AWS_REGION:-us-east-1}

read -p "Enter Neptune cluster name (default: multimodal-rag-kg): " CLUSTER_NAME
CLUSTER_NAME=${CLUSTER_NAME:-multimodal-rag-kg}

read -p "Enter VPC ID (or press Enter to use default VPC): " VPC_ID

read -p "Enter subnet group name (default: ${CLUSTER_NAME}-subnet-group): " SUBNET_GROUP_NAME
SUBNET_GROUP_NAME=${SUBNET_GROUP_NAME:-${CLUSTER_NAME}-subnet-group}

read -p "Enter security group name (default: ${CLUSTER_NAME}-sg): " SECURITY_GROUP_NAME
SECURITY_GROUP_NAME=${SECURITY_GROUP_NAME:-${CLUSTER_NAME}-sg}

read -p "Enter master username (default: admin): " MASTER_USERNAME
MASTER_USERNAME=${MASTER_USERNAME:-admin}

read -s -p "Enter master password: " MASTER_PASSWORD
echo

# Get default VPC if not specified
if [ -z "$VPC_ID" ]; then
    echo "🔍 Getting default VPC..."
    VPC_ID=$(aws ec2 describe-vpcs --region $AWS_REGION --filters "Name=is-default,Values=true" --query 'Vpcs[0].VpcId' --output text)
    echo "Using default VPC: $VPC_ID"
fi

# Get subnets
echo "🔍 Getting subnets..."
SUBNETS=$(aws ec2 describe-subnets --region $AWS_REGION --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[*].SubnetId' --output text | tr '\t' ',')

# Create subnet group
echo "📦 Creating subnet group..."
aws neptune create-db-subnet-group \
    --db-subnet-group-name $SUBNET_GROUP_NAME \
    --db-subnet-group-description "Subnet group for $CLUSTER_NAME" \
    --subnet-ids $SUBNETS \
    --region $AWS_REGION || echo "Subnet group may already exist"

# Create security group
echo "🔒 Creating security group..."
SECURITY_GROUP_ID=$(aws ec2 create-security-group \
    --group-name $SECURITY_GROUP_NAME \
    --description "Security group for $CLUSTER_NAME" \
    --vpc-id $VPC_ID \
    --region $AWS_REGION \
    --query 'GroupId' --output text 2>/dev/null || \
    aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=$SECURITY_GROUP_NAME" \
    --region $AWS_REGION \
    --query 'SecurityGroups[0].GroupId' --output text)

# Add inbound rules
echo "🔓 Adding inbound rules..."
aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp \
    --port 8182 \
    --cidr 0.0.0.0/0 \
    --region $AWS_REGION 2>/dev/null || echo "Rule may already exist"

# Create Neptune cluster
echo "🏗️  Creating Neptune cluster..."
CLUSTER_ARN=$(aws neptune create-db-cluster \
    --db-cluster-identifier $CLUSTER_NAME \
    --engine neptune \
    --engine-version 1.3.1.0 \
    --master-username $MASTER_USERNAME \
    --master-user-password $MASTER_PASSWORD \
    --db-subnet-group-name $SUBNET_GROUP_NAME \
    --vpc-security-group-ids $SECURITY_GROUP_ID \
    --backup-retention-period 1 \
    --region $AWS_REGION \
    --query 'DBCluster.DBClusterArn' --output text)

echo "⏳ Waiting for cluster to be available..."
aws neptune wait db-cluster-available \
    --db-cluster-identifier $CLUSTER_NAME \
    --region $AWS_REGION

# Create Neptune instance
echo "🏗️  Creating Neptune instance..."
aws neptune create-db-instance \
    --db-instance-identifier ${CLUSTER_NAME}-instance \
    --db-cluster-identifier $CLUSTER_NAME \
    --engine neptune \
    --db-instance-class db.r5.large \
    --region $AWS_REGION

echo "⏳ Waiting for instance to be available..."
aws neptune wait db-instance-available \
    --db-instance-identifier ${CLUSTER_NAME}-instance \
    --region $AWS_REGION

# Get cluster endpoint
echo "🔍 Getting cluster endpoint..."
CLUSTER_ENDPOINT=$(aws neptune describe-db-clusters \
    --db-cluster-identifier $CLUSTER_NAME \
    --region $AWS_REGION \
    --query 'DBClusters[0].Endpoint' --output text)

echo ""
echo "🎉 Neptune cluster created successfully!"
echo "======================================"
echo "Cluster Name: $CLUSTER_NAME"
echo "Cluster Endpoint: $CLUSTER_ENDPOINT"
echo "Region: $AWS_REGION"
echo "Security Group: $SECURITY_GROUP_ID"
echo ""
echo "📝 Add this to your local.env file:"
echo "NEPTUNE_CLUSTER_ENDPOINT=$CLUSTER_ENDPOINT"
echo "NEPTUNE_PORT=8182"
echo "NEPTUNE_REGION=$AWS_REGION"
echo "NEPTUNE_USE_SSL=true"
echo "NEPTUNE_VERIFY_SSL=true"
echo ""
echo "⚠️  Important:"
echo "- The cluster will take 5-10 minutes to be fully available"
echo "- You can monitor progress in the AWS Console"
echo "- Remember to delete the cluster when not in use to avoid charges"
echo ""
echo "🔗 Useful AWS Console links:"
echo "Neptune Dashboard: https://console.aws.amazon.com/neptune/home?region=$AWS_REGION#/databases"
echo "CloudWatch Logs: https://console.aws.amazon.com/cloudwatch/home?region=$AWS_REGION#logsV2:log-groups" 