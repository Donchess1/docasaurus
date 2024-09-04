#!/bin/bash
set -e

echo "Starting before_install.sh script"

# Create application directory if it doesn't exist
sudo mkdir -p /home/ec2-user/app
sudo chown ec2-user:ec2-user /home/ec2-user/app

# Hardcode ECR_REGISTRY
ECR_REGISTRY="654654197877.dkr.ecr.us-east-1.amazonaws.com"
echo "ECR_REGISTRY is set to: $ECR_REGISTRY"

# Login to ECR
echo "Attempting to log in to ECR"
if aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_REGISTRY; then
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
