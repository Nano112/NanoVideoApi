#!/bin/bash

# Production startup script for NanoVideoApi
set -e

echo "Starting NanoVideoApi in production mode..."

# Set default values if environment variables are not set
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}
WORKERS=${WORKERS:-4}
WORKER_CLASS=${WORKER_CLASS:-sanic.worker.GunicornWorker}

# Create logs directory if it doesn't exist
mkdir -p logs

# Start Gunicorn with Sanic
exec gunicorn \
    --bind $HOST:$PORT \
    --workers $WORKERS \
    --worker-class $WORKER_CLASS \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --timeout 120 \
    --keepalive 5 \
    --preload \
    --log-level info \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --capture-output \
    --enable-stdio-inheritance \
    src.app:app
