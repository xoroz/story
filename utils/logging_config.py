import os
import logging
from config_loader import load_config

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# Load configuration
config = load_config()

# Map string log levels to logging constants
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

def get_logger(name):
    """
    Get a logger configured according to settings in config.ini
    
    Args:
        name: Logger name (app, db_utils, story_processor, admin, email)
        
    Returns:
        logging.Logger: Configured logger
    """
    # Create logger
    logger = logging.getLogger(name)
    
    # Clear any existing handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # Get default log level
    default_level_str = config.get('Logging', 'default_log_level', fallback='INFO')
    default_level = LOG_LEVELS.get(default_level_str, logging.INFO)
    
    # Check for component-specific log level
    specific_level_key = f"{name}_log_level"
    if config.has_option('Logging', specific_level_key):
        level_str = config.get('Logging', specific_level_key)
        level = LOG_LEVELS.get(level_str, default_level)
    else:
        level = default_level
    
    # Set logger level
    logger.setLevel(level)
    
    # Get log file path
    log_file_key = f"{name}_log"
    if config.has_option('Logging', log_file_key):
        log_file = config.get('Logging', log_file_key)
    else:
        log_file = f"logs/{name}.log"
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Add file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    logger.addHandler(file_handler)
    
    # Add console handler if enabled
    console_logging = config.getboolean('Logging', 'console_logging', fallback=True)
    if console_logging:
        console_level_str = config.get('Logging', 'console_log_level', fallback='INFO')
        console_level = LOG_LEVELS.get(console_level_str, logging.INFO)
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(console_level)
        logger.addHandler(console_handler)
    
    # Prevent propagation to avoid duplicate logs
    logger.propagate = False
    
    return logger

def set_log_level(name, level):
    """
    Dynamically change the log level for a logger
    
    Args:
        name: Logger name
        level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    if level not in LOG_LEVELS:
        raise ValueError(f"Invalid log level: {level}")
    
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVELS[level])
    
    # Update handlers
    for handler in logger.handlers:
        handler.setLevel(LOG_LEVELS[level])
