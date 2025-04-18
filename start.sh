#!/bin/bash
# start the services 
# Set the working directory to script's location
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

P=bin/python3.12

# Create PID directory if it doesn't exist
mkdir -p pids
mkdir -p logs

# Export any environment variables needed
# If using virtual environment, uncomment and adjust the next line
# source bin/activate

# Start the Flask app in background
echo "Starting Flask App (port 8000)..."
$P app.py &
FLASK_PID=$!
echo "Flask App started with PID: $FLASK_PID"
echo $FLASK_PID > ./pids/app.pid

# Start the processor in background
echo "Starting Story Processor..."
$P story_processor.py &
PROCESSOR_PID=$!
echo "Story Processor started with PID: $PROCESSOR_PID"
echo $PROCESSOR_PID > ./pids/processor.pid

# Start the admin server in background
echo "Starting Admin Server (port 8001)..."
$P admin.py &
ADMIN_PID=$!
echo "Admin Server started with PID: $ADMIN_PID"
echo $ADMIN_PID > ./pids/admin.pid

echo "All services started. Check logs in logs/ directory"
echo "Main app: http://localhost:8000"
echo "Admin dashboard: http://localhost:8001 (login with admin/admin123 or configured credentials)"
