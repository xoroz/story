import sqlite3
import os
from config_loader import load_config

def init_db():
    """Initialize the database with the required tables."""
    # Load configuration
    config = load_config()
    
    # Connect to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Create users table from config
    if 'Database_Users' in config:
        table_name = config['Database_Users']['table_name']
        fields = config['Database_Users']['fields']
        
        cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            {fields}
        )
        ''')
        print(f"Created/updated {table_name} table")
    else:
        # Fallback to hardcoded structure if config section is missing
        initial_credits = int(config['User']['initial_credits'])
        cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            credits INTEGER DEFAULT {initial_credits},
            last_login TIMESTAMP,
            private BOOLEAN DEFAULT 0,
            auth_type TEXT DEFAULT 'local',
            preferred_language TEXT DEFAULT 'en'
        )
        ''')
        print("Created/updated users table (using fallback structure)")
    
    # Create user_stories table from config
    if 'Database_UserStories' in config:
        table_name = config['Database_UserStories']['table_name']
        fields = config['Database_UserStories']['fields']
        
        cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            {fields}
        )
        ''')
        print(f"Created/updated {table_name} table")
    else:
        # Fallback to hardcoded structure if config section is missing
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            story_filename TEXT NOT NULL,
            title TEXT,
            theme TEXT,
            theme_description TEXT,
            language TEXT,
            age_range TEXT,
            lesson TEXT,
            characters TEXT,
            story_about TEXT,
            ai_model TEXT,
            provider TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            output_file TEXT,
            audio_file TEXT,
            processing_time REAL,
            rating REAL DEFAULT 0,
            views INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        print("Created/updated user_stories table (using fallback structure)")
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print("Database initialized successfully!")

if __name__ == '__main__':
    init_db()
