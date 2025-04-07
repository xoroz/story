import os
import json
import sys
from datetime import datetime

# Path to the story metadata file
METADATA_FILE = 'story_metadata.json'

def ensure_directories_exist(config):
    """
    Ensure all required directories exist
    
    Args:
        config: Configuration dictionary with Paths section
    """
    # Get paths from config
    queue_folder = config['Paths']['queue_folder']
    output_folder = config['Paths']['output_folder']
    processed_folder = config['Paths']['processed_folder']
    error_folder = config['Paths']['error_folder']
    audio_folder = config['Paths'].get('audio_folder', os.path.join(output_folder, 'audio'))
    
    # Create directories if they don't exist
    os.makedirs(queue_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(processed_folder, exist_ok=True)
    os.makedirs(error_folder, exist_ok=True)
    os.makedirs(audio_folder, exist_ok=True)
    
    return {
        'queue_folder': queue_folder,
        'output_folder': output_folder,
        'processed_folder': processed_folder,
        'error_folder': error_folder,
        'audio_folder': audio_folder
    }

def get_story_metadata():
    """
    Get story metadata from the JSON file
    Creates the file with default structure if it doesn't exist
    
    Returns:
        dict: Story metadata
    """
    if not os.path.exists(METADATA_FILE):
        # Create default metadata structure
        metadata = {
            "metadata_version": 1,
            "stories": {}
        }
        # Save to file
        with open(METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        return metadata
    
    # Read existing metadata
    try:
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        # If file is corrupted, create a new one
        metadata = {
            "metadata_version": 1,
            "stories": {}
        }
        with open(METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        return metadata

def save_story_metadata(metadata):
    """
    Save story metadata to the JSON file
    
    Args:
        metadata: Metadata dictionary to save
    """
    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

def load_mcp():
    """
    Load the Model Control Protocol (MCP) JSON file.
    Fails with an error if the file is not found.
    
    Returns:
        dict: MCP configuration
    """
    mcp_path = 'child_storyteller_mcp.json'
    
    if not os.path.exists(mcp_path):
        print(f"ERROR: MCP file not found at {mcp_path}")
        print("The application requires this file to control AI behavior.")
        sys.exit(1)
        
    with open(mcp_path, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in MCP file: {e}")
            sys.exit(1)
