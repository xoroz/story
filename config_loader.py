import os
import sys
import configparser
from dotenv import load_dotenv

def load_config():
    """
    Load configuration from .env (for secrets) and config.ini (for app settings).
    Fails with an error if config.ini is not found.
    """
    # Load secrets from .env
    load_dotenv()
    
    # Load app config from config.ini
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    
    if not os.path.exists(config_path):
        print("ERROR: config.ini not found! The application requires a configuration file.")
        print(f"Expected location: {config_path}")
        print("Please create this file before running the application.")
        sys.exit(1)
    
    config.read(config_path)
    return config