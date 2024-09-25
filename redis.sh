#!/bin/bash

# Update and install Docker if not already installed
echo "Updating package database..."
sudo yum update -y

echo "Installing Docker..."
sudo yum install docker -y

# Add group membership for the default ec2-user so you can run all docker commands without using the sudo command:
sudo usermod -a -G docker ec2-user
id ec2-user
# Reload a Linux user's group assignments to docker w/o logout
newgrp docker
# Start Docker service and enable it to start at boot
echo "Starting Docker..."
sudo systemctl start docker
sudo systemctl enable docker

# Create Docker network if it doesn't exist
NETWORK_NAME="redis-network"
if [ ! "$(docker network ls | grep $NETWORK_NAME)" ]; then
  echo "Creating Docker network: $NETWORK_NAME"
  docker network create $NETWORK_NAME
else
  echo "Docker network $NETWORK_NAME already exists"
fi

# Create directories for persisting Redis data
echo "Creating directories for persisting Redis data..."
sudo mkdir -p /data/redis-staging /data/redis-prod
sudo chown -R $USER:$USER /data/redis-staging /data/redis-prod

# Pull Redis image if not already pulled
if [ ! "$(docker images -q redis)" ]; then
  echo "Pulling Redis Docker image..."
  docker pull redis
else
  echo "Redis Docker image already exists"
fi

# Run Redis container for staging environment
STAGING_CONTAINER="redis-staging"
STAGING_PORT=6380
if [ ! "$(docker ps -q -f name=$STAGING_CONTAINER)" ]; then
  echo "Running Redis container for staging on port $STAGING_PORT..."
  docker run -d --name $STAGING_CONTAINER --network $NETWORK_NAME -p $STAGING_PORT:6379 -v /data/redis-staging:/data redis
else
  echo "Staging Redis container is already running"
fi

# Run Redis container for production environment
PROD_CONTAINER="redis-prod"
PROD_PORT=6379
if [ ! "$(docker ps -q -f name=$PROD_CONTAINER)" ]; then
  echo "Running Redis container for production on port $PROD_PORT..."
  docker run -d --name $PROD_CONTAINER --network $NETWORK_NAME -p $PROD_PORT:6379 -v /data/redis-prod:/data redis
else
  echo "Production Redis container is already running"
fi

# List running containers for verification
echo "Listing running Redis containers..."
docker ps --filter "name=redis-"

echo "Setup complete!"