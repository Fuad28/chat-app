#!/bin/bash

# Wait for the database to be ready
while ! nc -z db 5432; do
  echo "Waiting for the PostgreSQL database..."
  sleep 1
done

# Navigate to the /app directory
cd /app

# Run pytest
echo "Running tests..."
pytest
