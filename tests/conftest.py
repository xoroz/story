import pytest
import os
import subprocess
import time
import requests
from pathlib import Path

# Base URL of the application
BASE_URL = "http://localhost:8000"

# Ensure test results directory exists
os.makedirs("test-results/videos", exist_ok=True)

# Configure Playwright
def pytest_configure(config):
    """Configure Playwright"""
    # If we haven't installed Playwright browsers, do it
    try:
        import playwright
        try:
            result = subprocess.run(["playwright", "install", "chromium"], 
                                   capture_output=True, text=True, check=True)
            print("Playwright browser installation result:", result.stdout)
        except subprocess.CalledProcessError:
            print("Error installing Playwright browsers. Trying to continue with existing installation.")
    except ImportError:
        print("Playwright not installed. Please run 'pip install playwright' and 'playwright install'")

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Override browser context args to disable video recording for faster tests"""
    return {
        **browser_context_args,
        "record_video_dir": None,  # Disable video recording for faster tests
    }

@pytest.fixture(scope="session", autouse=False)
def start_server():
    """Start the Flask application for testing (only if not already running)"""
    # Check if server is already running
    try:
        import requests
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            # Server is already running, no need to start it
            print("Server is already running")
            yield
            return
    except:
        # Server is not running, we need to start it
        pass
    
    print("Starting server for testing...")
    
    # Start the server using the start.sh script
    server_process = subprocess.Popen(["./start.sh"], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for the server to start
    max_retries = 10
    for i in range(max_retries):
        try:
            import requests
            response = requests.get(f"{BASE_URL}/")
            if response.status_code == 200:
                print(f"Server started successfully after {i+1} attempts")
                break
        except:
            print(f"Waiting for server to start (attempt {i+1}/{max_retries})...")
            time.sleep(1)
    
    # Yield to allow tests to run
    yield
    
    # After tests, stop the server using stop.sh
    print("Stopping server...")
    subprocess.run(["./stop.sh"], shell=True)

@pytest.fixture(scope="function")
def page(context):
    """Create a new page for each test"""
    page = context.new_page()
    yield page
    page.close()