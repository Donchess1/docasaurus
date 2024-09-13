#!/bin/bash
set -e

echo "Starting start_app.sh script"

# Change to the application directory
APP_DIR="/home/ec2-user/app"
cd $APP_DIR

# Copy .env.example to .env if it exists, otherwise create an empty .env
echo "Copying env.example to .env"
cp .env.example .env


update_env_var() {
    local param_name=$1
    local env_var_name=$2
    local value=$(aws ssm get-parameter --name "$param_name" --with-decryption --query Parameter.Value --output text)
    if grep -q "^$env_var_name=" .env; then
        # If the variable exists, update it
        sed -i "s|^$env_var_name=.*|$env_var_name=$value|" .env
    else
        # If the variable doesn't exist, add it

        echo "$env_var_name=$value" >> .env
    fi
}

# Source the ecr_info.env file
source ecr_info.env

if [ "$ENVIRONMENT" = "staging" ]; then
    ENV_SUFFIX="staging"
elif [ "$ENVIRONMENT" = "prod" ]; then
    ENV_SUFFIX="prod"
else
    echo "Unknown environment: $ENVIRONMENT"
    exit 1
fi
# Fetch sensitive data from Parameter Store and update .env
echo "Fetching sensitive data from Parameter Store and updating .env"

echo "" >> .env
echo "" >> .env

update_env_var "/mybalance/${ENV_SUFFIX}/POSTGRES_HOST" "POSTGRES_HOST"
update_env_var "/mybalance/${ENV_SUFFIX}/POSTGRES_USER" "POSTGRES_USER"
update_env_var "/mybalance/${ENV_SUFFIX}/POSTGRES_PASSWORD" "POSTGRES_PASSWORD"
update_env_var "/mybalance/${ENV_SUFFIX}/POSTGRES_DB" "POSTGRES_DB"
update_env_var "/mybalance/${ENV_SUFFIX}/POSTGRES_PORT" "POSTGRES_PORT"

update_env_var "/mybalance/${ENV_SUFFIX}/ENVIRONMENT" "ENVIRONMENT"
update_env_var "/mybalance/${ENV_SUFFIX}/DJANGO_SECRET_KEY" "DJANGO_SECRET_KEY"
update_env_var "/mybalance/${ENV_SUFFIX}/DJANGO_DEBUG" "DJANGO_DEBUG"
update_env_var "/mybalance/${ENV_SUFFIX}/DJANGO_ALLOWED_HOSTS" "DJANGO_ALLOWED_HOSTS"

update_env_var "/mybalance/${ENV_SUFFIX}/FRONTEND_BASE_URL" "FRONTEND_BASE_URL"
update_env_var "/mybalance/${ENV_SUFFIX}/BACKEND_BASE_URL" "BACKEND_BASE_URL"

update_env_var "/mybalance/${ENV_SUFFIX}/MERCHANT_REDIRECT_BASE_URL" "MERCHANT_REDIRECT_BASE_URL"
update_env_var "/mybalance/${ENV_SUFFIX}/CUSTOMER_WIDGET_BUYER_BASE_URL" "CUSTOMER_WIDGET_BUYER_BASE_URL"
update_env_var "/mybalance/${ENV_SUFFIX}/CUSTOMER_WIDGET_SELLER_BASE_URL" "CUSTOMER_WIDGET_SELLER_BASE_URL"

update_env_var "/mybalance/${ENV_SUFFIX}/FLW_SECRET_KEY" "FLW_SECRET_KEY"
update_env_var "/mybalance/${ENV_SUFFIX}/FLW_SECRET_HASH" "FLW_SECRET_HASH"

update_env_var "/mybalance/${ENV_SUFFIX}/CLOUDINARY_CLOUD_NAME" "CLOUDINARY_CLOUD_NAME"
update_env_var "/mybalance/${ENV_SUFFIX}/CLOUDINARY_API_KEY" "CLOUDINARY_API_KEY"
update_env_var "/mybalance/${ENV_SUFFIX}/CLOUDINARY_API_SECRET" "CLOUDINARY_API_SECRET"

update_env_var "/mybalance/${ENV_SUFFIX}/EMAIL_HOST_USER" "EMAIL_HOST_USER"
update_env_var "/mybalance/${ENV_SUFFIX}/EMAIL_HOST_PASSWORD" "EMAIL_HOST_PASSWORD"
update_env_var "/mybalance/${ENV_SUFFIX}/DEFAULT_FROM_EMAIL" "DEFAULT_FROM_EMAIL"

# Ensure correct permissions on .env file
chmod 600 .env

# Load ECR registry from ecr_registry.env if it exists, otherwise use hardcoded values
if [ -f "ecr_registry.env" ]; then
    echo "Loading ECR registry from ecr_registry.env"
    source ecr_registry.env
else
    echo "Warning: ecr_registry.env not found. Using hardcoded ECR values."
    ECR_REGISTRY="654654197877.dkr.ecr.us-east-1.amazonaws.com"
fi

ECR_REPOSITORY="mybalance-${ENV_SUFFIX}-api"

echo "Using ECR_REGISTRY: $ECR_REGISTRY"
echo "Using ECR_REPOSITORY: $ECR_REPOSITORY"

# Use docker compose yml file
COMPOSE_FILE="docker-compose-${ENV_SUFFIX}.yml"

echo "Using $COMPOSE_FILE"

# Pull the latest images
echo "Pulling latest images"
ECR_REGISTRY=$ECR_REGISTRY ECR_REPOSITORY=$ECR_REPOSITORY docker-compose -f $COMPOSE_FILE pull

# Start the application
echo "Starting the application"
ECR_REGISTRY=$ECR_REGISTRY ECR_REPOSITORY=$ECR_REPOSITORY docker-compose -f $COMPOSE_FILE up -d

echo "Application started successfully"

