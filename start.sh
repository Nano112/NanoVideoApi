#!/bin/bash

# Production startup script for NanoVideoApi
set -e

echo "Starting NanoVideoApi in production mode..."

# Set default values if environment variables are not set
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}
WORKERS=${WORKERS:-4}

# Create logs directory if it doesn't exist
mkdir -p logs

# Start Gunicorn with Sanic
exec gunicorn \
    --bind $HOST:$PORT \
    --workers $WORKERS \
    --worker-class sanic.worker.GunicornWorker \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --timeout 120 \
    --preload \
    --log-level info \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    src.app:app
