from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file, jsonify
from flask_wtf.csrf import CSRFProtect
import os
import json
from datetime import datetime

from config_loader import load_config
from auth import get_user_info, use_credit
from services.story_service import (
    create_story_request, save_story_request, check_story_status,
    get_story_content, extract_story_metadata, check_story_privacy,
    update_story_view_count, get_story_list, get_prefill_data_for_story
)
from utils.file_utils import load_mcp

# Create a Blueprint for story routes
story_bp = Blueprint('story', __name__)

# Load configuration
config = load_config()
QUEUE_FOLDER = config['Paths']['queue_folder']
OUTPUT_FOLDER = config['Paths']['output_folder']
PROCESSED_FOLDER = config['Paths']['processed_folder']
ERROR_FOLDER = config['Paths']['error_folder']
AUDIO_FOLDER = config['Paths'].get('audio_folder', os.path.join(OUTPUT_FOLDER, 'audio'))
CHECK_INTERVAL = int(config['App']['check_interval'])

@story_bp.route('/create', methods=['GET', 'POST'])
def create_story():
    """Story creation route"""
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please log in to create a story')
        return redirect(url_for('auth.login'))
    
    # Check if email is verified
    if not session.get('email_verified', False):
        flash('Please verify your email address before creating stories')
        return redirect(url_for('auth.registration_pending'))
        
    # Load MCP - will exit if not found
    mcp = load_mcp()
    
    if request.method == 'POST':
        # Create story request
        request_data, request_id, error = create_story_request(request.form, session['user_id'])
        
        if error:
            flash(error)
            return redirect(url_for('story.create_story'))
        
        # Store in session for reference
        session['request_data'] = request_data
        
        # Save to queue folder
        if not save_story_request(request_data, QUEUE_FOLDER):
            flash("Error saving story request")
            return redirect(url_for('story.create_story'))
        
        # Deduct credits from user account
        use_credit(session['user_id'])
        
        # Update session credits
        session['credits'] = session['credits'] - 1
            
        # Redirect to waiting page
        return redirect(url_for('story.waiting', request_id=request_id))
    
    # For GET requests, pass data to template
    themes = mcp.get("themes", {})
    lessons = mcp.get("lessons", [])
    ai_providers = mcp.get("ai_providers", {})
    
    # Get example stories from config
    try:
        example_stories_str = config['App'].get('example_stories', '[]')
        # Clean up the string to ensure it's valid JSON
        example_stories = json.loads(example_stories_str)
    except json.JSONDecodeError:
        print("Error parsing example_stories from config.ini")
        example_stories = []
    
    # Check if we have prefill data from recreate_story
    prefill_data = session.pop('prefill_data', None)
    
    return render_template(
        'create_story.html', 
        themes=themes, 
        lessons=lessons,
        ai_providers=ai_providers,
        prefill=prefill_data,
        example_stories=example_stories
    )

@story_bp.route('/recreate-story/<int:story_id>')
def recreate_story(story_id):
    """Recreate a story from an existing one"""
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please log in to recreate a story')
        return redirect(url_for('auth.login'))
    
    # Check if email is verified
    if not session.get('email_verified', False):
        flash('Please verify your email address before creating stories')
        return redirect(url_for('auth.registration_pending'))
    
    # Get prefill data for the story
    prefill_data = get_prefill_data_for_story(story_id)
    
    if not prefill_data:
        flash('Story not found')
        return redirect(url_for('auth.profile'))
    
    # Store prefill data in session
    session['prefill_data'] = prefill_data
    
    # Redirect to create story page
    return redirect(url_for('story.create_story'))

@story_bp.route('/waiting/<request_id>')
def waiting(request_id):
    """Waiting page for story generation"""
    # Check story status
    status, request_data, error = check_story_status(
        request_id, QUEUE_FOLDER, PROCESSED_FOLDER, ERROR_FOLDER
    )
    
    if status == 'processed' and 'output_file' in request_data:
        return redirect(url_for('story.view_story', filename=request_data['output_file']))
    
    if status == 'error':
        flash(f"Error creating story: {error}")
        return redirect(url_for('story.create_story'))
    
    if status == 'not_found':
        flash("Story request not found")
        return redirect(url_for('story.create_story'))
    
    # Get waiting messages from config
    try:
        waiting_messages_str = config['App'].get('waiting_messages', '["Please wait while we generate your story..."]')
        waiting_messages = json.loads(waiting_messages_str)
    except json.JSONDecodeError:
        # Fallback to default messages if JSON parsing fails
        waiting_messages = [
            "Please wait while we generate your story...",
            "Our AI is crafting a unique tale just for you...",
            "Creating characters and settings for your story...",
            "Weaving together an exciting plot...",
            "Adding educational elements to your story...",
            "Polishing the narrative for maximum enjoyment...",
            "Almost there! Finalizing your story...",
            "Just a moment more for story magic to happen..."
        ]
    
    # Convert waiting messages to JSON for JavaScript
    waiting_messages_json = json.dumps(waiting_messages)
    
    # If we get here, render waiting template
    return render_template(
        'waiting.html', 
        request_id=request_id, 
        title=request_data['parameters'].get('title', 'My Story'),
        backend=request_data.get('backend', 'openai'),
        ai_model=request_data['parameters'].get('ai_model', 'gpt-3.5-turbo'),
        check_interval=CHECK_INTERVAL * 1000,  # Convert to milliseconds for JS
        waiting_messages=waiting_messages_json  # Pass messages as JSON string
    )

@story_bp.route('/check-status/<request_id>')
def check_story_status_route(request_id):
    """Check the status of a story request"""
    # Check story status
    status, request_data, error = check_story_status(
        request_id, QUEUE_FOLDER, PROCESSED_FOLDER, ERROR_FOLDER
    )
    
    if status == 'processed' and 'output_file' in request_data:
        return redirect(url_for('story.view_story', filename=request_data['output_file']))
    
    if status == 'error':
        flash(f"Error creating story: {error}")
        return redirect(url_for('story.create_story'))
    
    # Still processing, continue waiting
    return redirect(url_for('story.waiting', request_id=request_id))

@story_bp.route('/stories')
def list_stories():
    """List all stories"""
    # Get list of stories
    stories = get_story_list(
        session.get('user_id'), 
        OUTPUT_FOLDER, 
        PROCESSED_FOLDER, 
        AUDIO_FOLDER
    )
    
    return render_template('story_list.html', stories=stories)

@story_bp.route('/stories/<filename>')
def view_story(filename):
    """View a story"""
    # Get story content
    content, error = get_story_content(filename, OUTPUT_FOLDER)
    
    if error:
        flash(error)
        return redirect(url_for('story.list_stories'))
    
    # Extract metadata from content
    metadata = extract_story_metadata(content, filename, PROCESSED_FOLDER, AUDIO_FOLDER)
    
    # Check if this story should be private
    user_id = metadata.get('user_id')
    
    # If the story has a user_id and it's not the current user
    if user_id and user_id != session.get('user_id'):
        # Check if the story is marked as private
        is_story_private = False
        request_id = metadata.get('request_id')
        if request_id:
            processed_path = os.path.join(PROCESSED_FOLDER, f"{request_id}.json")
            if os.path.exists(processed_path):
                try:
                    with open(processed_path, 'r') as f:
                        request_data = json.load(f)
                    # Check if the story is marked as private
                    is_story_private = request_data.get('parameters', {}).get('is_private', False)
                except Exception as e:
                    print(f"Error checking story privacy: {e}")
        
        # Get story ID if available
        story_id = None
        if request_id:
            # Try to find the story ID from the database
            from db_utils import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            result = cursor.execute(
                'SELECT id FROM user_stories WHERE story_filename = ?', 
                (filename,)
            ).fetchone()
            if result:
                story_id = result['id']
            conn.close()
        
        # Check if the story should be private
        is_private = check_story_privacy(story_id, user_id, session.get('user_id'))
        
        # If the story is private, redirect
        if is_private:
            flash('This story is private and can only be viewed by its creator')
            return redirect(url_for('story.list_stories'))
    
    # Increment view count
    story_meta = update_story_view_count(filename)
    
    # Get rating information
    ratings = story_meta.get('ratings', [])
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    rating_count = len(ratings)
    view_count = story_meta.get('views', 0)
    
    # Current date
    current_date = datetime.now().strftime('%B %d, %Y')
    
    # Render the story view template
    return render_template(
        'story_view.html',
        title=metadata.get('title', 'Story'),
        story_html=metadata.get('story_html', ''),
        story_about=metadata.get('story_about'),
        audio_path=metadata.get('audio_path'),
        provider_display=metadata.get('provider_display', 'AI'),
        model=metadata.get('model', 'Unknown'),
        current_date=current_date,
        filename=filename,
        avg_rating=avg_rating,
        rating_count=rating_count,
        view_count=view_count,
        username=metadata.get('username')
    )

@story_bp.route('/audio/<filename>')
def get_audio(filename):
    """Get audio file"""
    # Security check to prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        flash('Invalid audio filename')
        return redirect(url_for('story.list_stories'))
        
    file_path = os.path.join(AUDIO_FOLDER, filename)
    if not os.path.exists(file_path):
        flash('Audio not found')
        return redirect(url_for('story.list_stories'))
    
    return send_file(file_path)
