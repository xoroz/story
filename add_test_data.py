#!/usr/bin/env python3
"""
Add Test Data to Database

This script adds a test user and a test story to the database for testing purposes.
"""

import sqlite3
import os
import sys
from datetime import datetime
from flask_bcrypt import Bcrypt
from config_loader import load_config

# Initialize Flask-Bcrypt for password hashing
bcrypt = Bcrypt()

def get_db_connection(db_path='database.db'):
    """Get a connection to the SQLite database"""
    if not os.path.exists(db_path):
        print(f"Error: Database file '{db_path}' not found.")
        sys.exit(1)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def add_test_user():
    """Add a test user to the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if test user already exists
    cursor.execute("SELECT id FROM users WHERE username = ?", ("testuser",))
    user = cursor.fetchone()
    
    if user:
        print(f"Test user 'testuser' already exists with ID {user['id']}")
        conn.close()
        return user['id']
    
    # Create test user
    password_hash = bcrypt.generate_password_hash("testpassword").decode('utf-8')
    
    cursor.execute('''
    INSERT INTO users (username, email, password_hash, private, auth_type) 
    VALUES (?, ?, ?, ?, ?)
    ''', ("testuser", "test@example.com", password_hash, 0, "local"))
    
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    print(f"Created test user 'testuser' with ID {user_id}")
    return user_id

def add_test_story(user_id):
    """Add a test story to the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if test story already exists
    cursor.execute("SELECT id FROM user_stories WHERE title = ? AND user_id = ?", 
                  ("Test Story", user_id))
    story = cursor.fetchone()
    
    if story:
        print(f"Test story 'Test Story' already exists with ID {story['id']}")
        conn.close()
        return story['id']
    
    # Get table info to check available columns
    cursor.execute("PRAGMA table_info(user_stories)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Prepare story data
    story_data = {
        'user_id': user_id,
        'story_filename': 'test_story.html',
        'title': 'Test Story',
        'theme': 'Adventure',
        'theme_description': 'A thrilling adventure in a magical forest',
        'language': 'en',
        'age_range': '5-8',
        'lesson': 'Courage and friendship',
        'characters': 'Alex, Lily, and a talking fox',
        'story_about': 'Two children who discover a magical forest and make friends with a talking fox',
        'ai_model': 'Claude',
        'provider': 'Anthropic',
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'output_file': 'test_story.html',
        'audio_file': 'test_story.mp3',
        'processing_time': 2.5,
        'rating': 4.5,
        'views': 10
    }
    
    # Filter out fields that don't exist in the table
    fields = []
    values = []
    for field, value in story_data.items():
        if field in columns:
            fields.append(field)
            values.append(value)
    
    # Build and execute the query
    placeholders = ', '.join(['?' for _ in fields])
    query = f'''
    INSERT INTO user_stories (
        {', '.join(fields)}
    ) VALUES ({placeholders})
    '''
    
    cursor.execute(query, values)
    story_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    print(f"Created test story 'Test Story' with ID {story_id}")
    return story_id

def main():
    """Main function"""
    print("Adding test data to database...")
    print("=" * 80)
    
    # Add test user
    user_id = add_test_user()
    
    # Add test story
    story_id = add_test_story(user_id)
    
    print("=" * 80)
    print("Test data added successfully!")
    print(f"Test user ID: {user_id}")
    print(f"Test story ID: {story_id}")
    print("You can now log in with:")
    print("  Username: testuser")
    print("  Password: testpassword")

if __name__ == "__main__":
    main()
