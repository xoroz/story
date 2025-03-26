import os
import json
import uuid
import sys
import re
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify
from config_loader import load_config
#from admin import admin_bp

# Load configuration
config = load_config()

# Get API keys from .env (already loaded by load_config)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')

# Get app settings from config.ini
QUEUE_FOLDER = config['Paths']['queue_folder']
OUTPUT_FOLDER = config['Paths']['output_folder']
PROCESSED_FOLDER = config['Paths']['processed_folder']
ERROR_FOLDER = config['Paths']['error_folder']
AUDIO_FOLDER = config['Paths'].get('audio_folder', os.path.join(OUTPUT_FOLDER, 'audio'))
CHECK_INTERVAL = int(config['App']['check_interval'])

# Ensure directories exist
os.makedirs(QUEUE_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(ERROR_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = config['App']['secret_key']

# Register blueprints
#app.register_blueprint(admin_bp)

# Path to the story metadata file
METADATA_FILE = 'story_metadata.json'

def get_story_metadata():
    """
    Get story metadata from the JSON file
    Creates the file with default structure if it doesn't exist
    """
    if not os.path.exists(METADATA_FILE):
        # Create default metadata structure
        metadata = {
            "metadata_version": 1,
            "stories": {}
        }
        # Save to file
        with open(METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        return metadata
    
    # Read existing metadata
    try:
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        # If file is corrupted, create a new one
        metadata = {
            "metadata_version": 1,
            "stories": {}
        }
        with open(METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        return metadata

def save_story_metadata(metadata):
    """Save story metadata to the JSON file"""
    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

def load_mcp():
    """
    Load the Model Control Protocol (MCP) JSON file.
    Fails with an error if the file is not found.
    """
    mcp_path = 'child_storyteller_mcp.json'
    
    if not os.path.exists(mcp_path):
        print(f"ERROR: MCP file not found at {mcp_path}")
        print("The application requires this file to control AI behavior.")
        sys.exit(1)
        
    with open(mcp_path, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in MCP file: {e}")
            sys.exit(1)

def get_language_name(language_code):
    """Convert language code to language name"""
    language_map = {
        'en': 'English',
        'es': 'Spanish',
        'it': 'Italian',
        'pt': 'Portuguese',
        'pt-br': 'Portuguese-Brazil',
    }
    return language_map.get(language_code, 'Portuguese-Brazil')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create', methods=['GET', 'POST'])
def create_story():
    # Load MCP - will exit if not found
    mcp = load_mcp()
    
    if request.method == 'POST':
        # Get form data
        request_id = str(uuid.uuid4())
        
        # Get basic parameters
        theme_id = request.form.get('theme')
        age_range = request.form.get('age_range')
        length_setting = request.form.get('length', 'medium')
        language = request.form.get('language', 'en')
        lesson = request.form.get('lesson')
        characters = request.form.get('characters', '')
        story_about = request.form.get('story_about', '')
        
        # Look up theme description
        theme_map = mcp.get("themes", {})
        if theme_id not in theme_map:
            flash(f"Error: Selected theme '{theme_id}' not found in MCP")
            return redirect(url_for('create_story'))
        theme_description = theme_map[theme_id]
        
        # Get token limit based on length
        token_lengths = mcp.get('token_lengths', {})
        max_tokens = token_lengths.get(length_setting, 3000)
        
        # Create age-specific system prompt
        age_adaptations = mcp.get('age_adaptation', {})
        age_guidance = age_adaptations.get(age_range, "")
        
        # Build system prompt
        system_prompt = mcp.get('system_prompt', '')
        
        # Add age-specific guidance if available
        if age_guidance:
            system_prompt += f"\n\nFOR AGE RANGE {age_range}:\n{age_guidance}"
        
        # Add story structure guidance
        story_structure = mcp.get('story_structure', '')
        if story_structure:
            system_prompt += f"\n\nSTORY STRUCTURE:\n{story_structure}"
            
        # Add language instruction
        system_prompt += f"\n\nLANGUAGE:\nPlease write the story in {get_language_name(language)}."
        
        # Build user message from template
        user_template = mcp.get('user_template', '')
        if not user_template:
            flash("Error: User template not found in MCP")
            return redirect(url_for('create_story'))
            
        user_message = user_template.format(
            age_range=age_range,
            characters=characters,
            theme_description=theme_description,
            story_about=story_about,
            lesson=lesson,
            length=length_setting,
            tokens=max_tokens
        )
        
        # Create request data
        request_data = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "parameters": {
                "age_range": age_range,
                "theme": theme_id,
                "theme_description": theme_description,
                "lesson": lesson,
                "characters": characters,
                "story_about": story_about,
                "title": request.form.get('title', 'My Story'),
                "length": length_setting,
                "max_tokens": max_tokens,
                "language": language,
                "ai_model": request.form.get('ai_model', 'openai/gpt-3.5-turbo'),
                "enable_audio": request.form.get('enable_audio') == 'true'
            },
            "prompts": {
                "system_prompt": system_prompt,
                "user_message": user_message
            },
            "status": "pending",
            "backend": request.form.get('backend', 'openai')
        }
        
        # Store in session for reference
        session['request_data'] = request_data
        
        # Save to queue folder
        filename = f"{QUEUE_FOLDER}/{request_id}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(request_data, f, indent=2)
            
        # Redirect to waiting page
        return redirect(url_for('waiting', request_id=request_id))
    
    # For GET requests, pass data to template
    themes = mcp.get("themes", {})
    lessons = mcp.get("lessons", [])
    ai_providers = mcp.get("ai_providers", {})
    
    return render_template(
        'create_story.html', 
        themes=themes, 
        lessons=lessons,
        ai_providers=ai_providers
    )

@app.route('/waiting/<request_id>')
def waiting(request_id):
    # Check if request exists
    request_path = os.path.join(QUEUE_FOLDER, f"{request_id}.json")
    processed_path = os.path.join(PROCESSED_FOLDER, f"{request_id}.json")
    error_path = os.path.join(ERROR_FOLDER, f"{request_id}.json")
    
    request_data = None
    
    # Check if in queue
    if os.path.exists(request_path):
        with open(request_path, 'r') as f:
            request_data = json.load(f)
        status = "Processing"
    
    # Check if processed
    elif os.path.exists(processed_path):
        with open(processed_path, 'r') as f:
            request_data = json.load(f)
        
        if 'output_file' in request_data:
            return redirect(url_for('view_story', filename=request_data['output_file']))
        
        status = "Completed"
    
    # Check if error
    elif os.path.exists(error_path):
        with open(error_path, 'r') as f:
            request_data = json.load(f)
        
        flash(f"Error creating story: {request_data.get('error', 'Unknown error')}")
        return redirect(url_for('create_story'))
    
    # Not found
    else:
        flash("Story request not found")
        return redirect(url_for('create_story'))
    
    # Load MCP to get waiting messages
    mcp = load_mcp()
    waiting_messages = mcp.get('waiting_messages', [
        "We are working hard to create your amazing story...",
        "Please wait while we generate your story..."
    ])
    
    # Debug: Print waiting messages
    print(f"Waiting messages: {waiting_messages}")
    waiting_messages_json = json.dumps(waiting_messages)
    print(f"JSON waiting messages: {waiting_messages_json}")
    
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

@app.route('/check-status/<request_id>')
def check_story_status(request_id):
    # Check if the story is complete (in processed folder)
    processed_file = os.path.join(PROCESSED_FOLDER, f"{request_id}.json")
    
    if os.path.exists(processed_file):
        with open(processed_file, 'r') as f:
            request_data = json.load(f)
            
        # If output file is set, story is ready
        if 'output_file' in request_data:
            return redirect(url_for('view_story', filename=request_data['output_file']))
    
    # Check if there was an error
    error_file = os.path.join(ERROR_FOLDER, f"{request_id}.json")
    if os.path.exists(error_file):
        with open(error_file, 'r') as f:
            request_data = json.load(f)
        
        flash(f"Error creating story: {request_data.get('error', 'Unknown error')}")
        return redirect(url_for('create_story'))
    
    # Still processing, continue waiting
    return redirect(url_for('waiting', request_id=request_id))

@app.route('/stories')
def list_stories():
    # Get list of HTML files in stories directory
    story_files = []
    
    # Get story metadata
    metadata = get_story_metadata()
    stories_metadata = metadata.get('stories', {})
    
    for file in os.listdir(OUTPUT_FOLDER):
        if file.endswith('.html'):
            # Get creation time and simple name
            path = os.path.join(OUTPUT_FOLDER, file)
            created = datetime.fromtimestamp(os.path.getctime(path))
            
            # Extract title from filename (remove timestamp and extension)
            title = ' '.join(file.split('_')[:-1]).replace('-', ' ').title()
            
            # Get metadata for this story if available
            story_meta = stories_metadata.get(file, {})
            
            # Calculate average rating
            ratings = story_meta.get('ratings', [])
            avg_rating = sum(ratings) / len(ratings) if ratings else 0
            
            # Get view count
            view_count = story_meta.get('views', 0)
            
            # Try to find request_id from HTML content
            request_id = None
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Look for audio path which contains request_id
                audio_match = re.search(r'<source src="/audio/([a-f0-9-]+)\.mp3"', content)
                if audio_match:
                    request_id = audio_match.group(1)
            
            # Enhanced metadata from processed request
            theme = age = model = provider = processing_time = audio_size = language_code = None
            
            # If we have a request_id, try to load the processed request file
            if request_id:
                processed_path = os.path.join(PROCESSED_FOLDER, f"{request_id}.json")
                if os.path.exists(processed_path):
                    try:
                        with open(processed_path, 'r') as f:
                            request_data = json.load(f)
                            
                        # Extract additional metadata
                        params = request_data.get('parameters', {})
                        theme = params.get('theme', '')
                        age = params.get('age_range', '')
                        language_code = params.get('language', '')
                        
                        # Get AI model info
                        ai_info = request_data.get('ai_info', {})
                        provider = ai_info.get('provider', '')
                        model = ai_info.get('model', '')
                        
                        # Get processing time
                        timing = request_data.get('timing', {})
                        processing_time = timing.get('total_processing_seconds', 0)
                        
                        # Get audio file size if available
                        audio_file = request_data.get('audio_file')
                        if audio_file:
                            audio_path = os.path.join(AUDIO_FOLDER, audio_file)
                            if os.path.exists(audio_path):
                                audio_size = os.path.getsize(audio_path) / (1024 * 1024)  # Size in MB
                    except Exception as e:
                        # If there's an error, continue without the enhanced metadata
                        print(f"Error loading processed data for {request_id}: {e}")
            
            # Add all data to the story object
            story_files.append({
                'path': file,
                'title': title,
                'created': created,
                'avg_rating': avg_rating,
                'rating_count': len(ratings),
                'view_count': view_count,
                'request_id': request_id,
                'theme': theme,
                'age': age,
                'model': model,
                'provider': provider,
                'processing_time': processing_time,
                'audio_size': round(audio_size, 2) if audio_size else None,
                'has_audio': audio_size is not None,
                'language': get_language_name(language_code) if language_code else None
            })
    
    # Sort by creation time, newest first
    story_files.sort(key=lambda x: x['created'], reverse=True)
    
    return render_template('story_list.html', stories=story_files)

@app.route('/stories/<filename>')
def view_story(filename):
    # Security check to prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        flash('Invalid story filename')
        return redirect(url_for('list_stories'))
        
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    if not os.path.exists(file_path):
        flash('Story not found')
        return redirect(url_for('list_stories'))
    
    # Read the HTML file content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract title from the HTML content
    title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
    title = title_match.group(1) if title_match else 'Story'
    
    # Extract story content
    story_content_match = re.search(r'<div class="story-content">(.*?)</div>', content, re.DOTALL)
    story_html = story_content_match.group(1) if story_content_match else content
    
    # Extract story brief if available
    story_about = None
    story_about_match = re.search(r'<p class="story-about">(.*?)</p>', content, re.DOTALL)
    if story_about_match:
        story_about = story_about_match.group(1)
    
    # Extract audio path if available
    audio_path = None
    audio_match = re.search(r'<source src="/(.*?)" type="audio/mpeg">', content)
    if audio_match:
        audio_path = audio_match.group(1)
    
    # Extract provider and model info
    provider_display = 'AI'
    model = 'Unknown'
    ai_info_match = re.search(r'Created by (.*?) using (.*?)</div>', content)
    if ai_info_match:
        provider_display = ai_info_match.group(1)
        model = ai_info_match.group(2)
    
    # Current date
    current_date = datetime.now().strftime('%B %d, %Y')
    
    # Increment view count
    metadata = get_story_metadata()
    if filename not in metadata['stories']:
        metadata['stories'][filename] = {
            'ratings': [],
            'views': 0
        }
    
    # Increment view count
    metadata['stories'][filename]['views'] = metadata['stories'][filename].get('views', 0) + 1
    save_story_metadata(metadata)
    
    # Get rating information
    story_meta = metadata['stories'].get(filename, {})
    ratings = story_meta.get('ratings', [])
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    rating_count = len(ratings)
    view_count = story_meta.get('views', 0)
    
    # Render the story view template
    return render_template(
        'story_view.html',
        title=title,
        story_html=story_html,
        story_about=story_about,
        audio_path=audio_path,
        provider_display=provider_display,
        model=model,
        current_date=current_date,
        filename=filename,
        avg_rating=avg_rating,
        rating_count=rating_count,
        view_count=view_count
    )

@app.route('/rate-story', methods=['POST'])
def rate_story():
    """Handle story rating submissions via AJAX"""
    # Get form data
    filename = request.form.get('filename')
    rating = request.form.get('rating')
    
    # Validate input
    if not filename or not rating:
        return jsonify({'success': False, 'message': 'Missing required parameters'}), 400
    
    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            return jsonify({'success': False, 'message': 'Rating must be between 1 and 5'}), 400
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid rating value'}), 400
    
    # Security check to prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        return jsonify({'success': False, 'message': 'Invalid filename'}), 400
    
    # Check if the story exists
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'message': 'Story not found'}), 404
    
    # Get metadata
    metadata = get_story_metadata()
    
    # Initialize story metadata if not exists
    if filename not in metadata['stories']:
        metadata['stories'][filename] = {
            'ratings': [],
            'views': 0
        }
    
    # Add the rating
    metadata['stories'][filename]['ratings'].append(rating)
    
    # Calculate new average
    ratings = metadata['stories'][filename]['ratings']
    avg_rating = sum(ratings) / len(ratings)
    
    # Save metadata
    save_story_metadata(metadata)
    
    # Return success response with updated info
    return jsonify({
        'success': True,
        'message': 'Rating submitted successfully!',
        'average_rating': avg_rating,
        'rating_count': len(ratings)
    })

@app.route('/audio/<filename>')
def get_audio(filename):
    # Security check to prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        flash('Invalid audio filename')
        return redirect(url_for('list_stories'))
        
    file_path = os.path.join(AUDIO_FOLDER, filename)
    if not os.path.exists(file_path):
        flash('Audio not found')
        return redirect(url_for('list_stories'))
    
    return send_file(file_path)

if __name__ == '__main__':
    app.run(debug=True, port=8000, host='0.0.0.0')
