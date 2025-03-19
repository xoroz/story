import os
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change in production



# Configuration from environment
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')  # Add DeepSeek API key
QUEUE_FOLDER = os.getenv('QUEUE_FOLDER', 'queue')
OUTPUT_FOLDER = os.getenv('OUTPUT_FOLDER', 'stories')
PROCESSED_FOLDER = os.getenv('PROCESSED_FOLDER', 'processed')
ERROR_FOLDER = os.getenv('ERROR_FOLDER', 'errors')
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '10'))  # seconds

os.makedirs(QUEUE_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(ERROR_FOLDER, exist_ok=True)
os.makedirs(os.path.join(OUTPUT_FOLDER, 'audio'), exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create', methods=['GET', 'POST'])
def create_story():
    if request.method == 'POST':
        # Get form data
        request_id = str(uuid.uuid4())
        request_data = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "parameters": {
                "age_range": request.form.get('age_range'),
                "theme": request.form.get('theme'),
                "characters": request.form.get('characters'),
                "title": request.form.get('title', 'My Story'),
                "length": request.form.get('length', 'medium'),
                "language": request.form.get('language', 'en'),
                "ai_model": request.form.get('ai_model', 'gpt-3.5-turbo'),
                "enable_audio": request.form.get('enable_audio') == 'true'
            },
            "status": "pending",
            "backend": request.form.get('backend', 'openai')  # Get the selected backend
        }
        # Store in session for reference
        session['request_data'] = request_data
        
        # Save to queue folder
        filename = f"{QUEUE_FOLDER}/{request_id}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(request_data, f, indent=2)
            
        # Redirect to waiting page
        return redirect(url_for('waiting', request_id=request_id))
    
    return render_template('create_story.html')

@app.route('/waiting/<request_id>')
def waiting(request_id):
    # Check if request data is in session
    request_data = session.get('request_data', None)
    
    # If not in session, try to load from file
    if not request_data:
        queue_file = os.path.join(QUEUE_FOLDER, f"{request_id}.json")
        processed_file = os.path.join(PROCESSED_FOLDER, f"{request_id}.json")
        error_file = os.path.join(ERROR_FOLDER, f"{request_id}.json")
        
        if os.path.exists(queue_file):
            with open(queue_file, 'r') as f:
                request_data = json.load(f)
        elif os.path.exists(processed_file):
            with open(processed_file, 'r') as f:
                request_data = json.load(f)
                # Story is ready, redirect
                if 'output_file' in request_data:
                    return redirect(url_for('view_story', filename=request_data['output_file']))
        elif os.path.exists(error_file):
            with open(error_file, 'r') as f:
                request_data = json.load(f)
                # Error occurred, show error page
                flash(f"Error creating story: {request_data.get('error', 'Unknown error')}")
                return redirect(url_for('create_story'))
        
        if not request_data:
            flash("Story request not found.")
            return redirect(url_for('create_story'))
    
    # Render waiting page
    # Render waiting page with additional info
    return render_template(
        'waiting.html', 
        request_id=request_id, 
        title=request_data['parameters']['title'],
        backend=request_data.get('backend', 'openai'),
        ai_model=request_data['parameters']['ai_model']
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

@app.route('/confirmation')
def request_confirmation():
    request_data = session.get('request_data', None)
    if not request_data:
        flash('No story request found. Please create a new story.')
        return redirect(url_for('create_story'))
    
    return render_template('confirmation.html', request=request_data)

@app.route('/stories')
def list_stories():
    # Get list of HTML files in stories directory
    story_files = []
    for file in os.listdir(OUTPUT_FOLDER):
        if file.endswith('.html'):
            # Get creation time and simple name
            path = os.path.join(OUTPUT_FOLDER, file)
            created = datetime.fromtimestamp(os.path.getctime(path))
            
            # Extract title from filename (remove timestamp and extension)
            title = ' '.join(file.split('_')[:-1]).replace('-', ' ').title()
            
            story_files.append({
                'path': file,
                'title': title,
                'created': created
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
    
    # Simply serve the HTML file content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return content

@app.route('/audio/<filename>')
def serve_audio(filename):
    # Security check to prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        flash('Invalid audio filename')
        return redirect(url_for('list_stories'))
        
    file_path = os.path.join(OUTPUT_FOLDER, 'audio', filename)
    if not os.path.exists(file_path):
        flash('Audio file not found')
        return redirect(url_for('list_stories'))
    
    return send_file(file_path, mimetype='audio/mpeg')


if __name__ == '__main__':
    app.run(debug=True, port=8000, host='0.0.0.0')