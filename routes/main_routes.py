import random
import math
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g
from flask_babel import gettext as _
from config_loader import load_config

# Create a Blueprint for main routes
main_bp = Blueprint('main', __name__)

# Load configuration
config = load_config()

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

@main_bp.route('/about')
def about():
    """About page with version info and contact form"""
    # Get version from config
    version = config.get('App', 'version', fallback='1.0.0')
    
    # Generate a simple math question for human verification
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    operation = random.choice(['+', '-', '*'])
    
    if operation == '+':
        answer = num1 + num2
        question = f"{num1} + {num2}"
    elif operation == '-':
        # Ensure the result is positive
        if num1 < num2:
            num1, num2 = num2, num1
        answer = num1 - num2
        question = f"{num1} - {num2}"
    else:  # multiplication
        answer = num1 * num2
        question = f"{num1} × {num2}"
    
    # Store the answer in session for verification
    session['verification_answer'] = answer
    
    # Extract recent changes from activeContext.md
    recent_changes = []
    try:
        with open('memory-bank/activeContext.md', 'r') as f:
            content = f.read()
            # Find the Recent Changes section
            if '## Recent Changes' in content:
                changes_section = content.split('## Recent Changes')[1].split('##')[0].strip()
                # Split into paragraphs
                recent_changes = [p.strip() for p in changes_section.split('\n\n') if p.strip()]
    except Exception as e:
        recent_changes = [f"Error loading recent changes: {str(e)}"]
    
    return render_template('about.html', 
                          version=version, 
                          recent_changes=recent_changes,
                          verification_question=question)

@main_bp.route('/about/contact', methods=['POST'])
def contact():
    """Process contact form submission"""
    from services.email_service import send_contact_form_email
    
    # Get form data
    name = request.form.get('name', '')
    email = request.form.get('email', '')
    message = request.form.get('message', '')
    verification = request.form.get('verification', '')
    
    # Validate form data
    errors = []
    if not name:
        errors.append(_('Please enter your name'))
    if not email or '@' not in email:
        errors.append(_('Please enter a valid email address'))
    if not message:
        errors.append(_('Please enter a message'))
    if not verification:
        errors.append(_('Please answer the verification question'))
    
    # Check verification answer
    correct_answer = session.get('verification_answer')
    try:
        user_answer = int(verification)
        if user_answer != correct_answer:
            errors.append(_('Incorrect answer to verification question'))
    except (ValueError, TypeError):
        errors.append(_('Please enter a valid number for verification'))
    
    # If there are errors, flash them and redirect back to about page
    if errors:
        for error in errors:
            flash(error, 'error')
        return redirect(url_for('main.about'))
    
    # Send email
    success = send_contact_form_email(name, email, message, verification)
    
    if success:
        flash(_('Thank you for your message! We will get back to you soon.'), 'success')
    else:
        flash(_('There was an error sending your message. Please try again later.'), 'error')
    
    return redirect(url_for('main.about'))
