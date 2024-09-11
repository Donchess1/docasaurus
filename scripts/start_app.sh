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

# Fetch sensitive data from Parameter Store and update .env
echo "Fetching sensitive data from Parameter Store and updating .env"

echo "" >> .env
echo "" >> .env

update_env_var "/mybalance/staging/POSTGRES_HOST" "POSTGRES_HOST"
update_env_var "/mybalance/staging/POSTGRES_USER" "POSTGRES_USER"
# update_env_var "/mybalance/staging/POSTGRES_PASSWORD" "POSTGRES_PASSWORD"
# update_env_var "/mybalance/staging/POSTGRES_DB" "POSTGRES_DB"


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

ECR_REPOSITORY="mybalance-staging-api"

echo "Using ECR_REGISTRY: $ECR_REGISTRY"
echo "Using ECR_REPOSITORY: $ECR_REPOSITORY"

# Use docker-compose-staging.yml
COMPOSE_FILE="docker-compose-staging.yml"

echo "Using $COMPOSE_FILE"

# Pull the latest images
echo "Pulling latest images"
ECR_REGISTRY=$ECR_REGISTRY ECR_REPOSITORY=$ECR_REPOSITORY docker-compose -f $COMPOSE_FILE pull

# Start the application
echo "Starting the application"
ECR_REGISTRY=$ECR_REGISTRY ECR_REPOSITORY=$ECR_REPOSITORY docker-compose -f $COMPOSE_FILE up -d

echo "Application started successfully"

