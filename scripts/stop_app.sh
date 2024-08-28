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

# Check for docker-compose files and stop containers
if [ -f "docker-compose-staging.yml" ]; then
    stop_containers "docker-compose-staging.yml"
elif [ -f "docker-compose.yml" ]; then
    stop_containers "docker-compose.yml"
else
    echo "No docker-compose file found. Nothing to stop."
fi
docker system prune -af

echo "Application stopped"

