from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_bcrypt import Bcrypt
import sqlite3
import os
from config_loader import load_config

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
    
    # Create users table
    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        credits INTEGER DEFAULT {initial_credits},
        last_login TIMESTAMP
    )
    ''')
    
    # Create user_stories table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_stories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        story_filename TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
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

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                       (username, email, password_hash))
        conn.commit()
        conn.close()

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
            return redirect(url_for('index'))
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
    return redirect(url_for('index'))

# User profile route
@auth_bp.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Please log in to access your profile.')
        return redirect(url_for('auth.login'))

    return render_template('auth/profile.html', username=session['username'], credits=session['credits'])

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
