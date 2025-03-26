#!/bin/bash
# start the services 
# Set the working directory to script's location
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Create PID directory if it doesn't exist
mkdir -p pids
mkdir -p logs

# Export any environment variables needed
# If using virtual environment, uncomment and adjust the next line
# source bin/activate

# Start the Flask app in background
echo "Starting Flask App (port 8000)..."
python app.py > logs/app.log 2>&1 &
FLASK_PID=$!
echo "Flask App started with PID: $FLASK_PID"
echo $FLASK_PID > ./pids/app.pid

# Start the processor in background
echo "Starting Story Processor..."
python story_processor.py > logs/processor.log 2>&1 &
PROCESSOR_PID=$!
echo "Story Processor started with PID: $PROCESSOR_PID"
echo $PROCESSOR_PID > ./pids/processor.pid

# Start the admin server in background
echo "Starting Admin Server (port 8001)..."
python admin.py > logs/admin.log 2>&1 &
ADMIN_PID=$!
echo "Admin Server started with PID: $ADMIN_PID"
echo $ADMIN_PID > ./pids/admin.pid

echo "All services started. Check logs in logs/ directory"
echo "Main app: http://localhost:8000"
echo "Admin dashboard: http://localhost:8001 (login with admin/admin123 or configured credentials)"