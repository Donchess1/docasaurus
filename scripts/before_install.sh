#!/bin/bash
set -e

echo "Starting before_install.sh script"


# Fetch ECR_REGISTRY from Parameter Store
ECR_REGISTRY=$(aws ssm get-parameter --name "/mybalance/global/ECR_REGISTRY" --with-decryption --query Parameter.Value --output text)
echo "ECR_REGISTRY fetched: $ECR_REGISTRY"

# Login to ECR
echo "Attempting to log in to ECR"
if aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin $ECR_REGISTRY; then
    echo "Successfully logged in to ECR"
else
    echo "Failed to log in to ECR. Error code: $?"
    echo "Current AWS identity:"
    aws sts get-caller-identity
    echo "Listing ECR repositories:"
    aws ecr describe-repositories
    exit 1
fi

echo "before_install.sh script completed"
