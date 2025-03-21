#!/bin/bash

# Set the working directory
cd /home/felix/story/story2

# Kill the processes
if [ -f ./pids/app.pid ]; then
    APP_PID=$(cat ./pids/app.pid)
    echo "Stopping Flask App (PID: $APP_PID)..."
    kill $APP_PID
    rm ./pids/app.pid
fi

if [ -f ./pids/processor.pid ]; then
    PROCESSOR_PID=$(cat ./pids/processor.pid)
    echo "Stopping Story Processor (PID: $PROCESSOR_PID)..."
    kill $PROCESSOR_PID
    rm ./pids/processor.pid
fi

echo "All services stopped."