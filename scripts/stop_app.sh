#!/bin/bash
set -e

echo "Stopping application"

cd /home/ec2-user/app

# Function to stop containers
stop_containers() {
    local compose_file=$1
    echo "Stopping containers using $compose_file"
    # Use '|| true' to continue even if the command fails
    docker-compose -f $compose_file down || true
}

# Check if ecr_info.env exists
if [ ! -f "ecr_info.env" ]; then
    echo "ecr_info.env file not found. Please ensure it exists."
    exit 1
fi

# Source the ecr_info.env file
source ecr_info.env

# Check the environment
if [ "$ENVIRONMENT" = "staging" ]; then
    ENV_SUFFIX="-staging"
elif [ "$ENVIRONMENT" = "prod" ]; then
    ENV_SUFFIX="-prod"
else
    echo "Unknown environment: $ENVIRONMENT"
    exit 1
fi

# Use the appropriate docker-compose file
DOCKER_COMPOSE_FILE="docker-compose${ENV_SUFFIX}.yml"

if [ -f "$DOCKER_COMPOSE_FILE" ]; then
    stop_containers "$DOCKER_COMPOSE_FILE"
else
    echo "No $DOCKER_COMPOSE_FILE file found. Nothing to stop."
fi

docker system prune -af

echo "Application stopped"

