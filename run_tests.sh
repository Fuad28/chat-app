#!/bin/bash

# while ! nc -z db 5432; do
#   echo "Waiting for the PostgreSQL database..."
#   sleep 1
# done

cd /app

echo "Running tests..."
pytest
