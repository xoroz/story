#!/bin/bash

set -e  # Exit on error

# Create results directory if it doesn't exist
mkdir -p test-results/videos

export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0

# Print header
echo "========================================"
echo "Running StoryMagic Tests"
echo "========================================"
echo

# Check if playwright is installed
if ! python -c "import playwright" &> /dev/null; then
    echo "Playwright is not installed. Installing..."
    pip install playwright
fi

# Check if playwright browsers are installed
if ! playwright --version &> /dev/null; then
    echo "Installing Playwright browsers..."
    playwright install chromium
fi

# Check if the servers are already running
if curl -s http://localhost:8000 > /dev/null; then
    echo "Main application is running."
    MAIN_RUNNING=true
else
    echo "Starting main application for tests..."
    ./start.sh
    sleep 5 # Give more time for the server to start
    MAIN_RUNNING=false
fi

# Run the tests with pytest
echo "Running tests..."
python -m pytest tests/ -v --html=report.html

# Capture the exit code
TEST_EXIT_CODE=$?

# If we started the servers specifically for testing, stop them
if [ "$MAIN_RUNNING" = false ]; then
    echo "Stopping servers started for testing..."
    ./stop.sh
fi

# Print results
echo
echo "========================================"
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "All tests passed!"
else
    echo "Some tests failed. Check report.html for details."
fi
echo "========================================"

# Exit with the test exit code
exit $TEST_EXIT_CODE
