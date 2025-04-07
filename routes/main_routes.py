from flask import Blueprint, render_template, request, redirect, url_for, session, flash

# Create a Blueprint for main routes
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page route"""
    return render_template('index.html')

@main_bp.route('/admin/update-db', methods=['GET'])
def update_db():
    """
    Manually trigger database update from processed folder
    """
    # Check if user is logged in and is admin
    if 'user_id' not in session:
        flash('Please log in to access admin functions')
        return redirect(url_for('auth.login'))
    
    # Process all JSON files in the processed folder
    from db_utils import process_json_directory
    from config_loader import load_config
    
    config = load_config()
    processed_folder = config['Paths']['processed_folder']
    
    success_count, failure_count = process_json_directory(processed_folder)
    
    flash(f"Processed {success_count + failure_count} files: {success_count} successful, {failure_count} failed")
    return redirect(url_for('main.index'))
