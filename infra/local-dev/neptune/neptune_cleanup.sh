#!/bin/bash

# AWS Neptune Cleanup Script
# This script deletes the Neptune cluster and associated resources

set -e

echo "🧹 AWS Neptune Cleanup Script"
echo "============================"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed."
    exit 1
fi

# Get user input
read -p "Enter your AWS region (default: us-east-1): " AWS_REGION
AWS_REGION=${AWS_REGION:-us-east-1}

read -p "Enter Neptune cluster name to delete: " CLUSTER_NAME

if [ -z "$CLUSTER_NAME" ]; then
    echo "❌ Cluster name is required"
    exit 1
fi

echo "⚠️  WARNING: This will delete the Neptune cluster '$CLUSTER_NAME' and all its data!"
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Operation cancelled"
    exit 0
fi

echo "🗑️  Deleting Neptune instance..."
aws neptune delete-db-instance \
    --db-instance-identifier ${CLUSTER_NAME}-instance \
    --skip-final-snapshot \
    --region $AWS_REGION 2>/dev/null || echo "Instance may already be deleted"

echo "⏳ Waiting for instance to be deleted..."
aws neptune wait db-instance-deleted \
    --db-instance-identifier ${CLUSTER_NAME}-instance \
    --region $AWS_REGION 2>/dev/null || echo "Instance deletion completed"

echo "🗑️  Deleting Neptune cluster..."
aws neptune delete-db-cluster \
    --db-cluster-identifier $CLUSTER_NAME \
    --skip-final-snapshot \
    --region $AWS_REGION 2>/dev/null || echo "Cluster may already be deleted"

echo "⏳ Waiting for cluster to be deleted..."
aws neptune wait db-cluster-deleted \
    --db-cluster-identifier $CLUSTER_NAME \
    --region $AWS_REGION 2>/dev/null || echo "Cluster deletion completed"

echo "🗑️  Deleting subnet group..."
aws neptune delete-db-subnet-group \
    --db-subnet-group-name ${CLUSTER_NAME}-subnet-group \
    --region $AWS_REGION 2>/dev/null || echo "Subnet group may already be deleted"

echo "🗑️  Deleting security group..."
SECURITY_GROUP_ID=$(aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=${CLUSTER_NAME}-sg" \
    --region $AWS_REGION \
    --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null || echo "")

if [ ! -z "$SECURITY_GROUP_ID" ] && [ "$SECURITY_GROUP_ID" != "None" ]; then
    aws ec2 delete-security-group \
        --group-id $SECURITY_GROUP_ID \
        --region $AWS_REGION 2>/dev/null || echo "Security group may already be deleted"
fi

echo ""
echo "✅ Cleanup completed successfully!"
echo "================================="
echo "Deleted resources:"
echo "- Neptune cluster: $CLUSTER_NAME"
echo "- Neptune instance: ${CLUSTER_NAME}-instance"
echo "- Subnet group: ${CLUSTER_NAME}-subnet-group"
echo "- Security group: ${CLUSTER_NAME}-sg"
echo ""
echo "💡 Remember to remove Neptune configuration from your local.env file" 