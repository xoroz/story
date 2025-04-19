import os
import json
import sys
import shutil
import time
import subprocess
import re
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from configparser import ConfigParser
from config_loader import load_config
from utils.logging_config import get_logger

# Get logger for this component
logger = get_logger("admin")

# Load configuration
config = load_config()

# Create a separate Flask app for admin
admin_app = Flask(__name__)
admin_app.secret_key = config['App']['secret_key']

# Database connection function
def get_db_connection():
    """Get a connection to the SQLite database with row factory"""
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Get path information from config
OUTPUT_FOLDER = config['Paths']['output_folder']
QUEUE_FOLDER = config['Paths']['queue_folder']
PROCESSED_FOLDER = config['Paths']['processed_folder']
ERROR_FOLDER = config['Paths']['error_folder']
AUDIO_FOLDER = config['Paths'].get('audio_folder', os.path.join(OUTPUT_FOLDER, 'audio'))

# Get admin credentials from environment
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

# File paths
MCP_FILE = 'child_storyteller_mcp.json'
METADATA_FILE = 'story_metadata.json'
BACKUP_FOLDER = 'backups'

# Ensure backup directory exists
os.makedirs(BACKUP_FOLDER, exist_ok=True)

# Basic auth check function
def auth_required(func):
    """Decorator for routes that require authentication"""
    def wrapper(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != ADMIN_USERNAME or auth.password != ADMIN_PASSWORD:
            return 'Unauthorized', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'}
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@admin_app.route('/')
@auth_required
def admin_dashboard():
    """Admin dashboard main page"""
    now = datetime.now()
    return render_template('admin/dashboard.html', now=now)

@admin_app.route('/system')
@auth_required
def system_status():
    """System monitoring page"""
    # Check if processes are running
    app_running = False
    processor_running = False
    
    # Check app.py process
    app_pid_file = 'pids/app.pid'
    if os.path.exists(app_pid_file):
        with open(app_pid_file, 'r') as f:
            pid = f.read().strip()
            try:
                pid = int(pid)
                # Check if process is running
                os.kill(pid, 0)  # This will raise OSError if process is not running
                app_running = True
            except (ValueError, OSError):
                app_running = False
    
    # Check story_processor.py process
    processor_pid_file = 'pids/processor.pid'
    if os.path.exists(processor_pid_file):
        with open(processor_pid_file, 'r') as f:
            pid = f.read().strip()
            try:
                pid = int(pid)
                # Check if process is running
                os.kill(pid, 0)  # This will raise OSError if process is not running
                processor_running = True
            except (ValueError, OSError):
                processor_running = False
    
    # Get queue status
    queue_folder = config['Paths']['queue_folder']
    processed_folder = config['Paths']['processed_folder']
    error_folder = config['Paths']['error_folder']
    
    queue_count = len([f for f in os.listdir(queue_folder) if f.endswith('.json')]) if os.path.exists(queue_folder) else 0
    processed_count = len([f for f in os.listdir(processed_folder) if f.endswith('.json')]) if os.path.exists(processed_folder) else 0
    error_count = len([f for f in os.listdir(error_folder) if f.endswith('.json')]) if os.path.exists(error_folder) else 0
    
    # Get disk usage
    import shutil
    total, used, free = shutil.disk_usage('/')
    disk_usage = {
        'total': total // (1024 * 1024 * 1024),  # GB
        'used': used // (1024 * 1024 * 1024),    # GB
        'free': free // (1024 * 1024 * 1024),    # GB
        'percent': (used / total) * 100
    }
    
    return render_template(
        'admin/system.html',
        app_running=app_running,
        processor_running=processor_running,
        queue_count=queue_count,
        processed_count=processed_count,
        error_count=error_count,
        disk_usage=disk_usage
    )
    
@admin_app.route('/control_process', methods=['POST'])
@auth_required
def control_process():
    """Control (start/stop/restart) a process"""
    process = request.form.get('process')
    action = request.form.get('action')
    
    if not process or not action:
        flash("Missing process or action parameter")
        return redirect(url_for('system_status'))
    
    # Get log file paths from config
    app_log = config.get('Logging', 'app_log', fallback='logs/app.log')
    story_processor_log = config.get('Logging', 'story_processor_log', fallback='logs/story_processor.log')
    admin_log = config.get('Logging', 'admin_log', fallback='logs/admin.log')
    
    # Define process details
    processes = {
        'app': {
            'name': 'Web Application',
            'script': 'app.py',
            'pid_file': 'pids/app.pid',
            'log_file': app_log
        },
        'processor': {
            'name': 'Story Processor',
            'script': 'story_processor.py',
            'pid_file': 'pids/processor.pid',
            'log_file': story_processor_log
        },
        'admin': {
            'name': 'Admin Server',
            'script': 'admin.py',
            'pid_file': 'pids/admin.pid',
            'log_file': admin_log
        }
    }
    
    if process not in processes:
        flash(f"Unknown process: {process}")
        return redirect(url_for('system_status'))
    
    process_info = processes[process]
    
    # Handle different actions
    if action == 'stop':
        # Stop the process
        pid_file = process_info['pid_file']
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                pid = f.read().strip()
                try:
                    pid = int(pid)
                    # Check if process is running
                    try:
                        os.kill(pid, 0)  # This will raise OSError if process is not running
                        # Process exists, try to kill it
                        os.kill(pid, 15)  # SIGTERM
                        flash(f"{process_info['name']} stopped successfully")
                    except OSError:
                        flash(f"{process_info['name']} is not running")
                    
                    # Remove PID file
                    os.remove(pid_file)
                except ValueError:
                    flash(f"Invalid PID in {pid_file}")
        else:
            flash(f"{process_info['name']} is not running (no PID file)")
    
    elif action == 'start':
        # Start the process
        if process == 'admin':
            flash("Cannot start admin server (it's already running)")
        else:
            # Check if already running
            pid_file = process_info['pid_file']
            if os.path.exists(pid_file):
                flash(f"{process_info['name']} is already running")
            else:
                # Create directories if needed
                os.makedirs('pids', exist_ok=True)
                os.makedirs('logs', exist_ok=True)
                
                # Start the process
                cmd = f"python {process_info['script']} > {process_info['log_file']} 2>&1 &"
                proc = subprocess.Popen(cmd, shell=True)
                
                # Short sleep to allow process to start
                time.sleep(1)
                
                # For app.py and story_processor.py, we need to get the PID from the child process
                # In a real environment, we would use a better mechanism like process groups
                if process == 'app':
                    try:
                        # Find Python process running app.py
                        ps_output = subprocess.check_output(['ps', 'aux']).decode('utf-8')
                        for line in ps_output.split('\n'):
                            if 'python' in line and 'app.py' in line and 'grep' not in line:
                                pid = line.split()[1]
                                with open(pid_file, 'w') as f:
                                    f.write(pid)
                                break
                        flash(f"{process_info['name']} started successfully")
                    except Exception as e:
                        flash(f"Error getting PID for {process_info['name']}: {e}")
                
                elif process == 'processor':
                    try:
                        # Find Python process running story_processor.py
                        ps_output = subprocess.check_output(['ps', 'aux']).decode('utf-8')
                        for line in ps_output.split('\n'):
                            if 'python' in line and 'story_processor.py' in line and 'grep' not in line:
                                pid = line.split()[1]
                                with open(pid_file, 'w') as f:
                                    f.write(pid)
                                break
                        flash(f"{process_info['name']} started successfully")
                    except Exception as e:
                        flash(f"Error getting PID for {process_info['name']}: {e}")
    
    elif action == 'restart':
        if process == 'admin':
            # For admin server, just flash a message as we cannot restart ourselves
            flash("Admin server restart is not supported from the web interface. Please use the stop.sh and start.sh scripts.")
        else:
            # First stop the process
            pid_file = process_info['pid_file']
            if os.path.exists(pid_file):
                with open(pid_file, 'r') as f:
                    pid = f.read().strip()
                    try:
                        pid = int(pid)
                        # Check if process is running
                        try:
                            os.kill(pid, 0)  # This will raise OSError if process is not running
                            # Process exists, try to kill it
                            os.kill(pid, 15)  # SIGTERM
                        except OSError:
                            pass  # Process not running, continue to start
                        
                        # Remove PID file
                        os.remove(pid_file)
                    except ValueError:
                        pass  # Invalid PID, continue to start
            
            # Start the process
            os.makedirs('pids', exist_ok=True)
            os.makedirs('logs', exist_ok=True)
            
            # Start the process
            cmd = f"python {process_info['script']} > {process_info['log_file']} 2>&1 &"
            proc = subprocess.Popen(cmd, shell=True)
            
            # Short sleep to allow process to start
            time.sleep(1)
            
            # Get the PID of the process
            if process == 'app':
                try:
                    # Find Python process running app.py
                    ps_output = subprocess.check_output(['ps', 'aux']).decode('utf-8')
                    for line in ps_output.split('\n'):
                        if 'python' in line and 'app.py' in line and 'grep' not in line:
                            pid = line.split()[1]
                            with open(pid_file, 'w') as f:
                                f.write(pid)
                            break
                    flash(f"{process_info['name']} restarted successfully")
                except Exception as e:
                    flash(f"Error getting PID for {process_info['name']}: {e}")
            
            elif process == 'processor':
                try:
                    # Find Python process running story_processor.py
                    ps_output = subprocess.check_output(['ps', 'aux']).decode('utf-8')
                    for line in ps_output.split('\n'):
                        if 'python' in line and 'story_processor.py' in line and 'grep' not in line:
                            pid = line.split()[1]
                            with open(pid_file, 'w') as f:
                                f.write(pid)
                            break
                    flash(f"{process_info['name']} restarted successfully")
                except Exception as e:
                    flash(f"Error getting PID for {process_info['name']}: {e}")
    
    return redirect(url_for('system_status'))

@admin_app.route('/stories')
@auth_required
def manage_stories():
    """Story management page"""
    # Get story metadata
    metadata = {}
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    
    # Get story files
    output_folder = config['Paths']['output_folder']
    stories = []
    
    if os.path.exists(output_folder):
        for filename in os.listdir(output_folder):
            if filename.endswith('.html'):
                filepath = os.path.join(output_folder, filename)
                created = datetime.fromtimestamp(os.path.getctime(filepath))
                
                # Get metadata for this story
                story_meta = metadata.get('stories', {}).get(filename, {})
                
                # Calculate average rating
                ratings = story_meta.get('ratings', [])
                avg_rating = sum(ratings) / len(ratings) if ratings else 0
                
                # Try to find request_id from HTML content
                request_id = None
                username = None
                email = None
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Look for audio path which contains request_id
                    audio_match = re.search(r'<source src="/audio/([a-f0-9-]+)\.mp3"', content)
                    if audio_match:
                        request_id = audio_match.group(1)
                
                # If we have a request_id, try to load the processed request file
                if request_id:
                    processed_path = os.path.join(PROCESSED_FOLDER, f"{request_id}.json")
                    if os.path.exists(processed_path):
                        try:
                            with open(processed_path, 'r') as f:
                                request_data = json.load(f)
                            username = request_data.get('username', None)
                            email = request_data.get('email', None)
                        except Exception as e:
                            print(f"Error loading processed data for {request_id}: {e}")
                
                stories.append({
                    'filename': filename,
                    'title': ' '.join(filename.split('_')[:-1]).replace('-', ' ').title(),
                    'created': created,
                    'views': story_meta.get('views', 0),
                    'rating_count': len(ratings),
                    'avg_rating': avg_rating,
                    'username': username,
                    'email': email
                })
    
    # Sort by creation date, newest first
    stories.sort(key=lambda x: x['created'], reverse=True)
    
    return render_template('admin/stories.html', stories=stories)

@admin_app.route('/stories/delete/<filename>', methods=['POST'])
@auth_required
def delete_story(filename):
    """Delete a story"""
    # Security check to prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        flash('Invalid story filename')
        return redirect(url_for('manage_stories'))
    
    output_folder = config['Paths']['output_folder']
    filepath = os.path.join(output_folder, filename)
    
    if os.path.exists(filepath):
        # Delete the file
        os.remove(filepath)
        
        # Also delete from metadata
        if os.path.exists(METADATA_FILE):
            with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            if filename in metadata.get('stories', {}):
                del metadata['stories'][filename]
                
                # Save updated metadata
                with open(METADATA_FILE, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2)
        
        flash(f'Successfully deleted story: {filename}')
    else:
        flash(f'Story not found: {filename}')
    
    return redirect(url_for('manage_stories'))

@admin_app.route('/configuration')
@auth_required
def manage_config():
    """Configuration management page"""
    # Get MCP data
    mcp_data = {}
    if os.path.exists(MCP_FILE):
        with open(MCP_FILE, 'r', encoding='utf-8') as f:
            mcp_data = json.load(f)
    
    # Get config.ini data
    config_ini = {}
    config_ini_raw = ""
    if os.path.exists('config.ini'):
        # Read raw content for editing
        with open('config.ini', 'r', encoding='utf-8') as f:
            config_ini_raw = f.read()
            
        # Parse for display
        config_parser = ConfigParser()
        config_parser.read('config.ini')
        for section in config_parser.sections():
            config_ini[section] = {}
            for key, value in config_parser.items(section):
                config_ini[section][key] = value
    
    return render_template(
        'admin/configuration.html',
        mcp_data=mcp_data,
        config_ini=config_ini,
        config_ini_raw=config_ini_raw,
        mcp_json=json.dumps(mcp_data, indent=2)
    )

@admin_app.route('/configuration/update', methods=['POST'])
@auth_required
def update_mcp():
    """Update MCP configuration"""
    try:
        # Get the JSON data from the form
        mcp_json = request.form.get('mcp_json', '')
        
        # Parse the JSON to validate it
        mcp_data = json.loads(mcp_json)
        
        # Create a backup before updating
        if os.path.exists(MCP_FILE):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f"{BACKUP_FOLDER}/mcp_config_{timestamp}.json"
            shutil.copy2(MCP_FILE, backup_file)
        
        # Save the updated MCP file
        with open(MCP_FILE, 'w', encoding='utf-8') as f:
            json.dump(mcp_data, f, indent=2)
        
        flash('MCP configuration updated successfully')
    except json.JSONDecodeError as e:
        flash(f'Invalid JSON: {str(e)}')
    except Exception as e:
        flash(f'Error updating configuration: {str(e)}')
    
    return redirect(url_for('manage_config'))

@admin_app.route('/backup')
@auth_required
def backup_system():
    """Backup and restore page"""
    # Get list of existing backups
    backups = []
    
    if os.path.exists(BACKUP_FOLDER):
        for filename in os.listdir(BACKUP_FOLDER):
            filepath = os.path.join(BACKUP_FOLDER, filename)
            if os.path.isfile(filepath):
                created = datetime.fromtimestamp(os.path.getctime(filepath))
                size_kb = os.path.getsize(filepath) / 1024
                
                backups.append({
                    'filename': filename,
                    'created': created,
                    'size_kb': round(size_kb, 2)
                })
    
    # Sort by creation date, newest first
    backups.sort(key=lambda x: x['created'], reverse=True)
    
    return render_template('admin/backup.html', backups=backups)

@admin_app.route('/backup/create', methods=['POST'])
@auth_required
def create_backup():
    """Create a system backup"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"{BACKUP_FOLDER}/system_{timestamp}.zip"
        
        # Create a zip file containing important configuration files and data
        import zipfile
        with zipfile.ZipFile(backup_file, 'w') as zipf:
            # Add MCP file
            if os.path.exists(MCP_FILE):
                zipf.write(MCP_FILE)
            
            # Add config.ini
            if os.path.exists('config.ini'):
                zipf.write('config.ini')
            
            # Add story metadata
            if os.path.exists(METADATA_FILE):
                zipf.write(METADATA_FILE)
            
            # Add important directories
            for folder_name in ['templates', 'static']:
                if os.path.exists(folder_name):
                    for root, dirs, files in os.walk(folder_name):
                        for file in files:
                            file_path = os.path.join(root, file)
                            zipf.write(file_path)
        
        flash('Backup created successfully')
    except Exception as e:
        flash(f'Error creating backup: {str(e)}')
    
    return redirect(url_for('backup_system'))

@admin_app.route('/backup/download/<filename>')
@auth_required
def download_backup(filename):
    """Download a backup file"""
    # Security check to prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        flash('Invalid backup filename')
        return redirect(url_for('backup_system'))
    
    filepath = os.path.join(BACKUP_FOLDER, filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    else:
        flash(f'Backup file not found: {filename}')
        return redirect(url_for('backup_system'))

@admin_app.route('/backup/restore/<filename>', methods=['POST'])
@auth_required
def restore_backup(filename):
    """Restore from a backup file"""
    # Security check to prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        flash('Invalid backup filename')
        return redirect(url_for('backup_system'))
    
    filepath = os.path.join(BACKUP_FOLDER, filename)
    if not os.path.exists(filepath):
        flash(f'Backup file not found: {filename}')
        return redirect(url_for('backup_system'))
    
    try:
        # If it's a zip file, extract it
        if filename.endswith('.zip'):
            import zipfile
            with zipfile.ZipFile(filepath, 'r') as zipf:
                zipf.extractall('restore_temp')
            
            # Now copy the extracted files to their proper locations
            import os
            import shutil
            
            # Copy MCP file if it exists
            temp_mcp = os.path.join('restore_temp', MCP_FILE)
            if os.path.exists(temp_mcp):
                shutil.copy2(temp_mcp, MCP_FILE)
            
            # Copy config.ini if it exists
            temp_config = os.path.join('restore_temp', 'config.ini')
            if os.path.exists(temp_config):
                shutil.copy2(temp_config, 'config.ini')
            
            # Copy story metadata if it exists
            temp_metadata = os.path.join('restore_temp', METADATA_FILE)
            if os.path.exists(temp_metadata):
                shutil.copy2(temp_metadata, METADATA_FILE)
            
            # Clean up temporary directory
            shutil.rmtree('restore_temp')
        
        # If it's a JSON file, it's probably an MCP backup
        elif filename.endswith('.json'):
            if 'mcp_config' in filename:
                shutil.copy2(filepath, MCP_FILE)
        
        flash('Restore completed successfully')
    except Exception as e:
        flash(f'Error restoring from backup: {str(e)}')
    
    return redirect(url_for('backup_system'))

@admin_app.route('/backup/delete/<filename>', methods=['POST'])
@auth_required
def delete_backup(filename):
    """Delete a backup file"""
    # Security check to prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        flash('Invalid backup filename')
        return redirect(url_for('backup_system'))
    
    filepath = os.path.join(BACKUP_FOLDER, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        flash(f'Backup deleted: {filename}')
    else:
        flash(f'Backup file not found: {filename}')
    
    return redirect(url_for('backup_system'))

# User Management Routes
@admin_app.route('/users')
@auth_required
def manage_users():
    """User management page"""
    conn = get_db_connection()
    cursor = conn.cursor()
    users = cursor.execute('SELECT * FROM users ORDER BY id').fetchall()
    conn.close()
    
    # Convert to list of dictionaries
    user_list = [dict(user) for user in users]
    
    return render_template('admin/users.html', users=user_list)

@admin_app.route('/users/update_credits', methods=['POST'])
@auth_required
def update_user_credits():
    """Update user credits"""
    user_id = request.form.get('user_id')
    credits = request.form.get('credits')
    
    if not user_id or not credits:
        flash('Missing user ID or credits value')
        return redirect(url_for('manage_users'))
    
    try:
        # Validate inputs
        user_id = int(user_id)
        credits = int(credits)
        
        if credits < 0:
            flash('Credits cannot be negative')
            return redirect(url_for('manage_users'))
        
        # Update the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET credits = ? WHERE id = ?', (credits, user_id))
        conn.commit()
        conn.close()
        
        flash(f'Credits updated successfully for user ID {user_id}')
    except ValueError:
        flash('Invalid user ID or credits value')
    except Exception as e:
        flash(f'Error updating credits: {str(e)}')
    
    return redirect(url_for('manage_users'))

@admin_app.route('/users/delete', methods=['POST'])
@auth_required
def delete_user():
    """Delete a user"""
    user_id = request.form.get('user_id')
    
    if not user_id:
        flash('Missing user ID')
        return redirect(url_for('manage_users'))
    
    try:
        # Validate input
        user_id = int(user_id)
        
        # Delete the user
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First check if the user exists
        user = cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            conn.close()
            flash(f'User with ID {user_id} not found')
            return redirect(url_for('manage_users'))
        
        username = user['username']
        
        # Delete user's stories
        cursor.execute('DELETE FROM user_stories WHERE user_id = ?', (user_id,))
        
        # Delete the user
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        flash(f'User "{username}" (ID: {user_id}) deleted successfully')
    except ValueError:
        flash('Invalid user ID')
    except Exception as e:
        flash(f'Error deleting user: {str(e)}')
    
    return redirect(url_for('manage_users'))

@admin_app.route('/users/rename', methods=['POST'])
@auth_required
def rename_user():
    """Rename a user"""
    user_id = request.form.get('user_id')
    new_username = request.form.get('new_username')
    
    if not user_id or not new_username:
        flash('Missing user ID or new username')
        return redirect(url_for('manage_users'))
    
    try:
        # Validate input
        user_id = int(user_id)
        
        # Check if username is valid
        if not new_username.strip():
            flash('Username cannot be empty')
            return redirect(url_for('manage_users'))
        
        # Update the username
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First check if the user exists
        user = cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            conn.close()
            flash(f'User with ID {user_id} not found')
            return redirect(url_for('manage_users'))
        
        old_username = user['username']
        
        # Check if the new username already exists
        existing = cursor.execute('SELECT id FROM users WHERE username = ? AND id != ?', 
                                 (new_username, user_id)).fetchone()
        if existing:
            conn.close()
            flash(f'Username "{new_username}" is already taken')
            return redirect(url_for('manage_users'))
        
        # Update the username
        cursor.execute('UPDATE users SET username = ? WHERE id = ?', (new_username, user_id))
        conn.commit()
        conn.close()
        
        flash(f'Username changed from "{old_username}" to "{new_username}" successfully')
    except ValueError:
        flash('Invalid user ID')
    except Exception as e:
        flash(f'Error renaming user: {str(e)}')
    
    return redirect(url_for('manage_users'))

# JSON API endpoints for direct manipulation
@admin_app.route('/api/mcp', methods=['GET'])
@auth_required
def get_mcp():
    """Get MCP configuration as JSON"""
    if os.path.exists(MCP_FILE):
        with open(MCP_FILE, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    else:
        return jsonify({"error": "MCP file not found"}), 404

@admin_app.route('/api/mcp', methods=['POST'])
@auth_required
def set_mcp():
    """Update MCP configuration from JSON"""
    try:
        # Get JSON data from request
        data = request.json
        
        # Create a backup before updating
        if os.path.exists(MCP_FILE):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f"{BACKUP_FOLDER}/mcp_config_{timestamp}.json"
            shutil.copy2(MCP_FILE, backup_file)
        
        # Save the updated MCP file
        with open(MCP_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        return jsonify({"message": "MCP configuration updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
        
@admin_app.route('/configuration/update_config_ini', methods=['POST'])
@auth_required
def update_config_ini():
    """Update config.ini configuration"""
    try:
        # Get form data
        config_content = request.form.get('config_ini', '')
        
        # Basic validation - try to parse with ConfigParser
        config_parser = ConfigParser()
        config_parser.read_string(config_content)
        
        # Create a backup before updating
        if os.path.exists('config.ini'):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f"{BACKUP_FOLDER}/config_ini_{timestamp}.ini"
            shutil.copy2('config.ini', backup_file)
        
        # Save the updated config.ini file
        with open('config.ini', 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        flash('Configuration file updated successfully')
    except Exception as e:
        flash(f'Error updating configuration: {str(e)}')
    
    return redirect(url_for('manage_config'))

if __name__ == '__main__':
    admin_app.run(debug=True, port=8001, host='0.0.0.0')
