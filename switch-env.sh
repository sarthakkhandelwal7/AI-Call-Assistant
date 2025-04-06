#!/bin/bash

# Script to switch between development, testing, and production environments

# Display usage if no arguments provided
if [ $# -eq 0 ]; then
  echo "Usage: ./switch-env.sh [dev|test|prod]"
  exit 1
fi

ENV=$1

# Validate environment argument
if [[ "$ENV" != "dev" && "$ENV" != "test" && "$ENV" != "prod" ]]; then
  echo "Invalid environment: $ENV"
  echo "Usage: ./switch-env.sh [dev|test|prod]"
  exit 1
fi

echo "Switching to $ENV environment..."

# Stop any running containers
echo "Stopping current containers..."
docker-compose down

# Set environment variable and start containers
echo "Starting $ENV environment..."
APP_ENV=$ENV docker-compose up -d

echo "Environment switched to $ENV"
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3001"
echo "PgAdmin:  http://localhost:5050"

if [ "$ENV" == "test" ]; then
  echo ""
  echo "Testing mode is active. Run stress tests with:"
  echo "docker exec -it ai-call-assistant-backend-1 python tests/stress_tests/run_tests.py --test-type [test_type]"
fi 