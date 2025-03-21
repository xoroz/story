#!/bin/bash
# start the services 
# Set the working directory
cd /home/felix/story/story2

# Export any environment variables needed
#export PYTHONPATH=.
source bin/activate

# Start the Flask app in background
echo "Starting Flask App..."
nohup python3.12 app.py > logs/app.log 2>&1 &
FLASK_PID=$!
echo "Flask App started with PID: $FLASK_PID"
echo $FLASK_PID > ./pids/app.pid

# Start the processor in background
echo "Starting Story Processor..."
nohup python3.12 story_processor.py > logs/processor.log 2>&1 &
PROCESSOR_PID=$!
echo "Story Processor started with PID: $PROCESSOR_PID"
echo $PROCESSOR_PID > ./pids/processor.pid

echo "All services started. Check logs in logs/ directory"