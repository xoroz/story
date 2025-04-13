from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_babel import gettext as _
from flask_bcrypt import Bcrypt
import sqlite3
import os
import json
import secrets
import hashlib
import time
from datetime import datetime, timedelta
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
    
    # Check if columns exist in users table
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
    
    # Add preferred_language column if it doesn't exist
    if 'preferred_language' not in columns and 'id' in columns:
        print("Adding 'preferred_language' column to users table")
        cursor.execute("ALTER TABLE users ADD COLUMN preferred_language TEXT DEFAULT 'en'")
    
    # Add email_verified column if it doesn't exist
    if 'email_verified' not in columns and 'id' in columns:
        print("Adding 'email_verified' column to users table")
        cursor.execute("ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT 0")
    
    # Add verification_token column if it doesn't exist
    if 'verification_token' not in columns and 'id' in columns:
        print("Adding 'verification_token' column to users table")
        cursor.execute("ALTER TABLE users ADD COLUMN verification_token TEXT")
    
    # Add token_expiry column if it doesn't exist
    if 'token_expiry' not in columns and 'id' in columns:
        print("Adding 'token_expiry' column to users table")
        cursor.execute("ALTER TABLE users ADD COLUMN token_expiry TIMESTAMP")
    
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
    print("Register route accessed")
    if request.method == 'POST':
        print("Register POST request received")
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password_confirm = request.form['password_confirm']
        
        # Validate passwords match
        if password != password_confirm:
            flash(_('Passwords do not match.'))
            return render_template('auth/register.html')
        
        # Validate password strength
        if len(password) < 8:
            flash(_('Password must be at least 8 characters long.'))
            return render_template('auth/register.html')
        
        # Check for at least one uppercase, one lowercase, and one number
        if not (any(c.isupper() for c in password) and 
                any(c.islower() for c in password) and 
                any(c.isdigit() for c in password)):
            flash(_('Password must contain at least one uppercase letter, one lowercase letter, and one number.'))
            return render_template('auth/register.html')
        
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # Default values for new fields
        private = False
        auth_type = 'local'
        email_verified = False

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if username or email already exists
        existing_user = cursor.execute(
            'SELECT id FROM users WHERE username = ? OR email = ?', 
            (username, email)
        ).fetchone()
        
        if existing_user:
            conn.close()
            flash(_('Username or email already exists.'))
            return render_template('auth/register.html')
        
        # Insert new user
        cursor.execute('''
        INSERT INTO users (username, email, password_hash, private, auth_type, email_verified) 
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, email, password_hash, private, auth_type, email_verified))
        
        # Get the new user's ID
        user_id = cursor.lastrowid
        conn.commit()
        
        # Generate verification token
        token = set_verification_token(user_id)
        
        conn.close()

        # Send welcome email with verification link
        try:
            # Construct verification URL
            config = load_config()
            base_url = config['App']['url']
            verification_url = f"{base_url}/auth/verify/{token}"
            
            send_welcome_email(email, username, verification_url)
            
            flash(_('Registration successful! Please check your email to verify your account.'))
            return redirect(url_for('auth.registration_pending'))
        except Exception as e:
            print(f"Error sending welcome email: {e}")
            flash(_('Registration successful, but there was an error sending the verification email. Please contact support.'))
            return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

# Registration pending route
@auth_bp.route('/registration-pending')
def registration_pending():
    return render_template('auth/registration_pending.html')

# Email verification route
@auth_bp.route('/verify/<token>')
def verify_email(token):
    success, message = verify_token(token)
    
    if success:
        # If user is logged in, update their session
        if 'user_id' in session:
            session['email_verified'] = True
            
        flash(_('Your email has been verified successfully! You can now log in and create stories.'))
        return redirect(url_for('auth.email_verified'))
    else:
        flash(_(message))
        return redirect(url_for('auth.verification_failed'))

# Email verified confirmation page
@auth_bp.route('/email-verified')
def email_verified():
    return render_template('auth/email_verified.html')

# Verification failed page
@auth_bp.route('/verification-failed')
def verification_failed():
    return render_template('auth/verification_failed.html')

# User login route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        # Check if input matches username or email
        user = cursor.execute('SELECT * FROM users WHERE username = ? OR email = ?', 
                             (username_or_email, username_or_email)).fetchone()
        conn.close()

        if user and bcrypt.check_password_hash(user['password_hash'], password):
            # Set session variables
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['credits'] = user['credits']
            
            # Check if email is verified and set a session flag
            email_verified = bool(user['email_verified']) if 'email_verified' in user.keys() else False
            session['email_verified'] = email_verified
            
            # Show appropriate message
            if not email_verified:
                flash(_('Login successful! Please verify your email address to create stories.'))
            else:
                flash(_('Login successful!'))
                
            return redirect(url_for('main.index'))
        else:
            flash(_('Invalid username/email or password.'))

    return render_template('auth/login.html')

# User logout route
@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('credits', None)
    session.pop('email_verified', None)
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
        preferred_language=user_info.get('preferred_language', 'en'),
        email_verified=user_info.get('email_verified', False),
        user_stories=user_stories
    )

# Resend verification email route
@auth_bp.route('/resend-verification', methods=['GET', 'POST'])
def resend_verification():
    # If user is logged in, use their info directly
    if 'user_id' in session:
        user_id = session['user_id']
        user_info = get_user_info(user_id)
        
        # Check if email is already verified
        if user_info.get('email_verified', False):
            flash(_('Your email is already verified.'))
            return redirect(url_for('auth.profile'))
        
        # Generate new verification token
        token = set_verification_token(user_id)
        
        # Send verification email
        try:
            # Construct verification URL
            config = load_config()
            base_url = config['App']['url']
            verification_url = f"{base_url}/auth/verify/{token}"
            
            send_welcome_email(user_info['email'], user_info['username'], verification_url)
            
            flash(_('Verification email has been resent. Please check your inbox.'))
        except Exception as e:
            print(f"Error sending verification email: {e}")
            flash(_('Error sending verification email. Please try again later.'))
        
        return redirect(url_for('auth.profile'))
    
    # If user is not logged in, show a form to enter email
    if request.method == 'POST':
        email = request.form.get('email')
        
        # Find user by email
        conn = get_db_connection()
        cursor = conn.cursor()
        user = cursor.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        
        if not user:
            conn.close()
            flash(_('No account found with that email address.'))
            return render_template('auth/resend_verification.html')
        
        # Check if email is already verified
        if user['email_verified']:
            conn.close()
            flash(_('This email is already verified. Please log in.'))
            return redirect(url_for('auth.login'))
        
        # Generate new verification token
        token = set_verification_token(user['id'])
        conn.close()
        
        # Send verification email
        try:
            # Construct verification URL
            config = load_config()
            base_url = config['App']['url']
            verification_url = f"{base_url}/auth/verify/{token}"
            
            send_welcome_email(email, user['username'], verification_url)
            
            flash(_('Verification email has been sent. Please check your inbox.'))
            return redirect(url_for('auth.registration_pending'))
        except Exception as e:
            print(f"Error sending verification email: {e}")
            flash(_('Error sending verification email. Please try again later.'))
            return render_template('auth/resend_verification.html')
    
    # GET request - show the form
    return render_template('auth/resend_verification.html')

# Update profile route
@auth_bp.route('/update-profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        flash('Please log in to update your profile.')
        return redirect(url_for('auth.login'))
    
    # Get form data
    private = 'private' in request.form
    preferred_language = request.form.get('preferred_language', 'en')
    
    # Update user settings
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE users SET private = ?, preferred_language = ? WHERE id = ?',
        (1 if private else 0, preferred_language, session['user_id'])
    )
    conn.commit()
    conn.close()
    
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

# Function to generate a verification token
def generate_verification_token(user_id):
    """Generate a secure verification token"""
    # Create a random component
    random_component = secrets.token_urlsafe(32)
    
    # Combine with user ID and timestamp
    timestamp = int(time.time())
    data = f"{user_id}:{timestamp}:{random_component}"
    
    # Hash the data for security
    token_hash = hashlib.sha256(data.encode()).hexdigest()
    
    return token_hash

# Function to set verification token for a user
def set_verification_token(user_id):
    """Generate and store a verification token for a user"""
    token = generate_verification_token(user_id)
    
    # Set token expiry to 24 hours from now
    expiry = datetime.now() + timedelta(hours=24)
    expiry_str = expiry.strftime('%Y-%m-%d %H:%M:%S')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE users SET verification_token = ?, token_expiry = ? WHERE id = ?',
        (token, expiry_str, user_id)
    )
    conn.commit()
    conn.close()
    
    return token

# Function to verify a token
def verify_token(token):
    """Verify a token and mark the user's email as verified if valid"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Find user with this token
    user = cursor.execute(
        'SELECT id, token_expiry FROM users WHERE verification_token = ?',
        (token,)
    ).fetchone()
    
    if not user:
        conn.close()
        return False, "Invalid verification token"
    
    # Check if token has expired
    if user['token_expiry']:
        expiry = datetime.strptime(user['token_expiry'], '%Y-%m-%d %H:%M:%S')
        if expiry < datetime.now():
            conn.close()
            return False, "Verification token has expired"
    
    # Mark email as verified
    cursor.execute(
        'UPDATE users SET email_verified = 1, verification_token = NULL, token_expiry = NULL WHERE id = ?',
        (user['id'],)
    )
    conn.commit()
    conn.close()
    
    return True, "Email verified successfully"

# Function to check if a user's email is verified
def is_email_verified(user_id):
    """Check if a user's email is verified"""
    conn = get_db_connection()
    cursor = conn.cursor()
    result = cursor.execute(
        'SELECT email_verified FROM users WHERE id = ?',
        (user_id,)
    ).fetchone()
    conn.close()
    
    return bool(result and result['email_verified'])

# Function to get user information by user_id
def get_user_info(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    user = cursor.execute('SELECT id, username, email, private, auth_type, preferred_language, email_verified FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    if user:
        return {
            'user_id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'private': bool(user['private']) if 'private' in user.keys() else False,
            'auth_type': user['auth_type'] if 'auth_type' in user.keys() else 'local',
            'preferred_language': user['preferred_language'] if 'preferred_language' in user.keys() else 'en',
            'email_verified': bool(user['email_verified']) if 'email_verified' in user.keys() else False
        }
    return None
