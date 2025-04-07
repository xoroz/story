from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_bcrypt import Bcrypt
import sqlite3
import os
import json
from config_loader import load_config
from services.email_service import send_welcome_email

# Initialize Flask-Bcrypt
bcrypt = Bcrypt()

# Create a Blueprint for authentication
auth_bp = Blueprint('auth', __name__)

# Initialize database
def init_db():
    """Initialize the database with the required tables."""
    # Load configuration
    config = load_config()
    
    # Get initial credits from config
    initial_credits = int(config['User']['initial_credits'])
    
    # Connect to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Check if private and auth_type columns exist in users table
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Create users table if it doesn't exist
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
        auth_type TEXT DEFAULT 'local'
    )
    ''')
    
    # Add private column if it doesn't exist
    if 'private' not in columns and 'id' in columns:
        print("Adding 'private' column to users table")
        cursor.execute("ALTER TABLE users ADD COLUMN private BOOLEAN DEFAULT 0")
    
    # Add auth_type column if it doesn't exist
    if 'auth_type' not in columns and 'id' in columns:
        print("Adding 'auth_type' column to users table")
        cursor.execute("ALTER TABLE users ADD COLUMN auth_type TEXT DEFAULT 'local'")
    
    # Check if is_private column exists in user_stories table
    cursor.execute("PRAGMA table_info(user_stories)")
    story_columns = [column[1] for column in cursor.fetchall()]
    
    # Add is_private column to user_stories if it doesn't exist
    if 'is_private' not in story_columns and 'id' in story_columns:
        print("Adding 'is_private' column to user_stories table")
        cursor.execute("ALTER TABLE user_stories ADD COLUMN is_private BOOLEAN DEFAULT 0")
    
    # Create user_stories table from config
    config = load_config()
    if 'Database_UserStories' in config:
        table_name = config['Database_UserStories']['table_name']
        fields = config['Database_UserStories']['fields']
        
        cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            {fields}
        )
        ''')
        print(f"Created/updated {table_name} table from config")
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

# Initialize the database when the module is imported
init_db()

# Database connection function
def get_db_connection():
    conn = sqlite3.connect('database.db')  # Update with your database path
    conn.row_factory = sqlite3.Row
    return conn

# User registration route
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    print("Login route accessed")
    if request.method == 'POST':
        print("Login POST request received")
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # Default values for new fields
        private = False
        auth_type = 'local'

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO users (username, email, password_hash, private, auth_type) 
        VALUES (?, ?, ?, ?, ?)
        ''', (username, email, password_hash, private, auth_type))
        conn.commit()
        conn.close()

        # Send welcome email
        try:
            send_welcome_email(email, username)
        except Exception as e:
            print(f"Error sending welcome email: {e}")
            # Don't fail registration if email fails

        flash('Registration successful! Please log in.')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

# User login route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        user = cursor.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and bcrypt.check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['credits'] = user['credits']
            flash('Login successful!')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid username or password.')

    return render_template('auth/login.html')

# User logout route
@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('credits', None)
    flash('You have been logged out successfully.')
    return redirect(url_for('main.index'))

# User profile route
@auth_bp.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Please log in to access your profile.')
        return redirect(url_for('auth.login'))
    
    # Get user info including private setting
    user_info = get_user_info(session['user_id'])
    
    # Get user stories with privacy settings
    from db_utils import get_stories_for_user
    user_stories = get_stories_for_user(session['user_id'])
    
    return render_template(
        'auth/profile.html', 
        username=session['username'], 
        credits=session['credits'],
        private=user_info.get('private', False),
        user_stories=user_stories
    )

# Update profile route
@auth_bp.route('/update-profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        flash('Please log in to update your profile.')
        return redirect(url_for('auth.login'))
    
    # Get form data
    private = 'private' in request.form
    
    # Update user settings
    from db_utils import update_user_private_setting
    update_user_private_setting(session['user_id'], private)
    
    flash('Profile updated successfully!')
    return redirect(url_for('auth.profile'))

# Update story privacy route
@auth_bp.route('/update-story-privacy', methods=['POST'])
def update_story_privacy():
    if 'user_id' not in session:
        flash('Please log in to update story privacy.')
        return redirect(url_for('auth.login'))
    
    # Get form data
    story_id = request.form.get('story_id')
    is_private = 'is_private' in request.form
    
    if not story_id:
        flash('Invalid story ID.')
        return redirect(url_for('auth.profile'))
    
    # Update story privacy setting
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # First check if the story belongs to the current user
    story = cursor.execute(
        'SELECT user_id FROM user_stories WHERE id = ?', 
        (story_id,)
    ).fetchone()
    
    if not story or story['user_id'] != session['user_id']:
        conn.close()
        flash('You do not have permission to update this story.')
        return redirect(url_for('auth.profile'))
    
    # Update the privacy setting
    cursor.execute(
        'UPDATE user_stories SET is_private = ? WHERE id = ?', 
        (1 if is_private else 0, story_id)
    )
    conn.commit()
    conn.close()
    
    flash('Story privacy updated successfully!')
    return redirect(url_for('auth.profile'))

# Function to deduct credits
def use_credit(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET credits = credits - 1 WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

# Function to add credits
def add_credits(user_id, amount):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET credits = credits + ? WHERE id = ?', (amount, user_id))
    conn.commit()
    conn.close()

# Function to get user credits
def get_user_credits(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    credits = cursor.execute('SELECT credits FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return credits['credits'] if credits else 0

# Function to associate a story with a user
def add_user_story(user_id, story_filename, is_private=False, **kwargs):
    """
    Associate a story with a user, with optional additional fields
    
    Args:
        user_id: The user ID
        story_filename: The story filename
        is_private: Whether the story is private (default: False)
        **kwargs: Additional fields to insert (title, theme, etc.)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get table info to check available columns
    cursor.execute("PRAGMA table_info(user_stories)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Start with required fields
    fields = ['user_id', 'story_filename', 'is_private']
    values = [user_id, story_filename, 1 if is_private else 0]
    
    # Add any additional fields that exist in the table
    for field, value in kwargs.items():
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
    conn.commit()
    conn.close()

# Function to get user information by user_id
def get_user_info(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    user = cursor.execute('SELECT id, username, email, private, auth_type FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    if user:
        return {
            'user_id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'private': bool(user['private']) if 'private' in user.keys() else False,
            'auth_type': user['auth_type'] if 'auth_type' in user.keys() else 'local'
        }
    return None
