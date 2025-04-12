from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g

# Create a Blueprint for main routes
main_bp = Blueprint('main', __name__)

@main_bp.route('/set-language')
def set_language():
    """Set the user's preferred language"""
    lang = request.args.get('lang', 'en')
    
    # Validate language code
    if lang not in ['en', 'es', 'pt', 'it']:
        lang = 'en'
    
    # If user is logged in, update their preferred language in the database
    if 'user_id' in session:
        from auth import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET preferred_language = ? WHERE id = ?',
            (lang, session['user_id'])
        )
        conn.commit()
        conn.close()
    
    # Store language in session for non-logged in users
    session['language'] = lang
    
    # Redirect back to the referring page or home page
    next_url = request.args.get('next') or request.referrer or url_for('main.index')
    return redirect(next_url)

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
