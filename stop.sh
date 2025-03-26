#!/bin/bash

# Set the working directory to script's location
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Function to stop a service
stop_service() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        echo "Stopping $service_name (PID: $pid)..."
        
        # Check if process exists
        if ps -p $pid > /dev/null; then
            kill $pid
            echo "$service_name stopped."
        else
            echo "$service_name is not running."
        fi
        
        # Remove PID file
        rm "$pid_file"
    else
        echo "$service_name is not running (no PID file)."
    fi
}

# Stop all services
stop_service "./pids/app.pid" "Flask App"
stop_service "./pids/processor.pid" "Story Processor"
stop_service "./pids/admin.pid" "Admin Server"

echo "All services stopped."