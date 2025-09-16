#!/bin/bash

# start_gunicorn.sh - Properly detaches gunicorn from SSH session using double fork pattern

# Configuration - these can be passed as arguments
WORKER_NUM=${1:-2}
ADDRESS=${2:-'127.0.0.1'}
PORT=${3:-5000}
TIMEOUT=${4:-180}
KEEPALIVE=${5:-10}
MAX_REQUESTS=${6:-1000}
MAX_REQUESTS_JITTER=${7:-50}
LOG_LEVEL=${8:-'debug'}
APP_NAME=${9:-'read-ai'}

# Set PATH to include local bin
export PATH=/home/$(whoami)/.local/bin:$PATH

# Kill existing gunicorn processes
echo "Killing existing gunicorn processes..."
pkill -f "gunicorn app:app" || true

# Wait a moment for processes to terminate
sleep 2

# Double fork pattern to completely detach the process
echo "Starting gunicorn server..."
(
    # First fork - create new process group
    setsid bash -c "
        # Second fork - completely detach from terminal
        (
            exec gunicorn app:app \
                -w $WORKER_NUM \
                -b $ADDRESS:$PORT \
                --timeout $TIMEOUT \
                --keep-alive $KEEPALIVE \
                --max-requests $MAX_REQUESTS \
                --max-requests-jitter $MAX_REQUESTS_JITTER \
                --log-level $LOG_LEVEL \
                < /dev/null \
                >> log/$APP_NAME.log 2>> log/$APP_NAME.err
        ) &
        # Exit immediately after starting the background process
        exit 0
    "
) &

# Wait briefly and check if process started successfully
sleep 1

# Verify gunicorn is running
if pgrep -f "gunicorn app:app" > /dev/null; then
    echo "Gunicorn server started successfully"
    exit 0
else
    echo "Failed to start gunicorn server"
    exit 1
fi