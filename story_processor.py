import os
import json
import time
import openai
from datetime import datetime
import logging
from dotenv import load_dotenv
import requests  # Add this for DeepSeek API

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("story_processor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("StoryProcessor")

# Load environment variables
load_dotenv()

# Configuration from environment
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY') 
QUEUE_FOLDER = os.getenv('QUEUE_FOLDER', 'queue')
OUTPUT_FOLDER = os.getenv('OUTPUT_FOLDER', 'stories')
PROCESSED_FOLDER = os.getenv('PROCESSED_FOLDER', 'processed')
ERROR_FOLDER = os.getenv('ERROR_FOLDER', 'errors')
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '10'))  # seconds

# Ensure directories exist
os.makedirs(QUEUE_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(ERROR_FOLDER, exist_ok=True)

# Load MCP configuration
def load_mcp():
    mcp_path = 'child_storyteller_mcp.json'
    if not os.path.exists(mcp_path):
        logger.warning(f"MCP file not found at {mcp_path}. Creating default configuration.")
        # Create a default MCP file
        default_mcp = {
            "system_prompt": {
                "ai_definition": {
                    "who_am_i": "I am a friendly storyteller for children",
                    "what_i_do": "I create original stories for children"
                },
                "ai_personality": {
                    "communication_style": "I use simple, clear language appropriate for children."
                },
                "ai_behavior": {
                    "what_to_avoid": "I avoid scary content and inappropriate themes"
                }
            }
        }
        with open(mcp_path, 'w') as f:
            json.dump(default_mcp, f, indent=2)
        return default_mcp
        
    with open(mcp_path, 'r') as f:
        return json.load(f)

# Generate story using OpenAI
def generate_story(request_data):

    mcp = load_mcp()
    
    # Get parameters
    params = request_data['parameters']
    age_range = params['age_range']
    theme = params['theme']
    characters = params['characters']
    length = params['length']
    language = params['language']
    ai_model = params['ai_model']
    
    # Create system prompt and user message
    system_prompt = f"""
    {mcp['system_prompt']['ai_definition']['who_am_i']}
    
    WHAT I DO:
    {mcp['system_prompt']['ai_definition']['what_i_do']}
    
    HOW I COMMUNICATE:
    {mcp['system_prompt']['ai_personality']['communication_style']}
    
    IMPORTANT CONSTRAINTS:
    {mcp['system_prompt']['ai_behavior']['what_to_avoid']}
    
    LANGUAGE:
    Please write the story in {get_language_name(language)}.
    """
    
    user_message = f"""
    Please create a {length} story for a child in the age range {age_range}.
    
    Theme: {theme}
    Characters: {characters}
    
    The story should be engaging, age-appropriate, and have a positive message.
    Write the entire story in {get_language_name(language)}.
    """
    
    # Check if API key is available
    if not OPENAI_API_KEY:
        logger.warning("No OpenAI API key found. Returning dummy story.")
        return f"Once upon a time, there was a story about {theme} with characters like {characters}. This is a placeholder because no OpenAI API key was provided."
    
    # Configure the API key
    openai.api_key = OPENAI_API_KEY
    
    try:
        # For o1-mini model, combine system prompt and user message
        if ai_model == 'o1-mini':
            combined_message = f"{system_prompt}\n\n{user_message}"
            messages = [
                {"role": "user", "content": combined_message}
            ]
        else:
            # For other models, use separate system and user messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        
        # Make the API call
        response = openai.chat.completions.create(
            model=ai_model,
            messages=messages,
            max_tokens=2000,
            temperature=0.7
        )
        
        # Return the generated story
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Error generating story: {e}")
        raise

# Generate story using DeepSeek
def generate_story_deepseek(request_data):
    """Generate a story using DeepSeek API"""
    mcp = load_mcp()
    
    # Get parameters
    params = request_data['parameters']
    age_range = params['age_range']
    theme = params['theme']
    characters = params['characters']
    length = params['length']
    language = params['language']
    ai_model = params['ai_model']
    
    # Create system prompt and user message
    system_prompt = f"""
    {mcp['system_prompt']['ai_definition']['who_am_i']}
    
    WHAT I DO:
    {mcp['system_prompt']['ai_definition']['what_i_do']}
    
    HOW I COMMUNICATE:
    {mcp['system_prompt']['ai_personality']['communication_style']}
    
    IMPORTANT CONSTRAINTS:
    {mcp['system_prompt']['ai_behavior']['what_to_avoid']}
    
    LANGUAGE:
    Please write the story in {get_language_name(language)}.
    """
    
    user_message = f"""
    Please create a {length} story for a child in the age range {age_range}.
    
    Theme: {theme}
    Characters: {characters}
    
    The story should be engaging, age-appropriate, and have a positive message.
    Write the entire story in {get_language_name(language)}.
    """
    
    # Check if API key is available
    if not DEEPSEEK_API_KEY:
        logger.warning("No DeepSeek API key found. Returning dummy story.")
        return f"Once upon a time, there was a story about {theme} with characters like {characters}. This is a placeholder because no DeepSeek API key was provided."
    
    try:
        # Map DeepSeek model names to actual API model names
        model_mapping = {
            'deepseek-chat': 'deepseek-chat',
            'deepseek-coder': 'deepseek-coder'
        }
        
        model = model_mapping.get(ai_model, 'deepseek-chat')
        
        # Set up the API request
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        # Make the API request
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=payload
        )
        
        # Check for errors
        if response.status_code != 200:
            logger.error(f"DeepSeek API error: {response.status_code} - {response.text}")
            raise Exception(f"DeepSeek API error: {response.status_code} - {response.text}")
        
        # Parse the response
        response_data = response.json()
        story = response_data['choices'][0]['message']['content']
        
        return story
        
    except Exception as e:
        logger.error(f"Error generating story with DeepSeek: {e}")
        raise

# Helper function to get full language name
def get_language_name(code):
    languages = {
        'en': 'English',
        'pt-br': 'Brazilian Portuguese',
        'pt': 'Portuguese',
        'it': 'Italian',
        'es': 'Spanish'
    }
    return languages.get(code, 'English')

# Add this function to story_processor.py
def generate_audio(text, language, request_id):
    """Generate audio narration using OpenAI's API"""
    if not OPENAI_API_KEY:
        logger.warning("No OpenAI API key found. Skipping audio generation.")
        return None
        
    try:
        voice_mapping = {
            'en': 'alloy',  # English default
            'pt-br': 'shimmer',  # Portuguese
            'pt': 'shimmer',  # Portuguese
            'it': 'nova',    # Italian
            'es': 'nova'     # Spanish
        }
        
        voice = voice_mapping.get(language, 'alloy')
        
        # Create audio directory if needed
        audio_dir = os.path.join(OUTPUT_FOLDER, 'audio')
        os.makedirs(audio_dir, exist_ok=True)
        
        # Create audio file path
        audio_filename = f"{request_id}.mp3"
        audio_path = os.path.join(audio_dir, audio_filename)
        
        # Call OpenAI TTS API
        response = openai.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        
        # Save the audio file
        response.stream_to_file(audio_path)
        
        logger.info(f"Audio generated: {audio_filename}")
        return f"audio/{audio_filename}"
        
    except Exception as e:
        logger.error(f"Error generating audio: {e}")
        return None

# Convert story to HTML
# Update this function in story_processor.py
def story_to_html(story, title, request_id, audio_path=None, language='en'):
    paragraphs = story.split('\n\n')
    html_paragraphs = [f"<p>{p}</p>" for p in paragraphs if p.strip()]
    
    # Add audio player if audio is available
    audio_html = ""
    if audio_path:
        audio_html = f"""
        <div class="audio-player">
            <h3>Listen to the story:</h3>
            <audio controls style="width: 100%; margin: 20px 0;">
                <source src="/{audio_path}" type="audio/mpeg">
                Your browser does not support the audio element.
            </audio>
        </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html lang="{language}">
    <head>
        <title>{title}</title>
        <meta charset="UTF-8">
        <style>
            body {{ 
                font-family: 'Comic Sans MS', cursive, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f9f9f9;
                color: #333;
                line-height: 1.6;
            }}
            h1 {{ 
                color: #FF6B6B;
                text-align: center;
            }}
            p {{ 
                font-size: 18px;
                margin-bottom: 15px;
            }}
            .story-container {{
                background-color: white;
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }}
            .date {{
                text-align: right;
                font-style: italic;
                margin-top: 30px;
                color: #888;
            }}
            .metadata {{
                margin-top: 20px;
                font-size: 14px;
                color: #888;
                text-align: center;
            }}
            .audio-player {{
                margin-top: 30px;
                padding: 20px;
                background-color: #f5f5f5;
                border-radius: 10px;
            }}
            .audio-player h3 {{
                color: #555;
                margin-top: 0;
            }}
        </style>
    </head>
    <body>
        <div class="story-container">
            <h1>{title}</h1>
            {''.join(html_paragraphs)}
            {audio_html}
            <div class="date">Created on {datetime.now().strftime('%B %d, %Y')}</div>
        </div>
        <div class="metadata">
            <p>Story ID: {request_id}</p>
        </div>
    </body>
    </html>
    """
    return html
# Process a single request file
def process_request(request_file):
    request_path = os.path.join(QUEUE_FOLDER, request_file)
    request_id = os.path.splitext(request_file)[0]
    
    logger.info(f"Processing request: {request_id}")
    
    try:
        # Read the request
        with open(request_path, 'r') as f:
            request_data = json.load(f)
        # Get backend type
        backend = request_data.get('backend', 'openai')
        # Generate the story based on backend
        if backend == 'deepseek':
            logger.info(f"Using DeepSeek backend for request: {request_id}")
            story = generate_story_deepseek(request_data)
        else:
            logger.info(f"Using OpenAI backend for request: {request_id}")
            story = generate_story(request_data)  # Original OpenAI function
        
        # Get story parameters
        params = request_data['parameters']
        title = params['title']
        language = params.get('language', 'en')
        enable_audio = params.get('enable_audio', False)
        
        # Generate audio if requested
        audio_path = None
        if enable_audio:
            logger.info(f"Generating audio for request: {request_id}")
            audio_path = generate_audio(story, language, request_id)
        
        # Convert to HTML
        html = story_to_html(story, title, request_id, audio_path, language)
        
        # Create filename for the story
        safe_title = title.lower().replace(' ', '-')
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        html_filename = f"{safe_title}_{timestamp}.html"
        html_path = os.path.join(OUTPUT_FOLDER, html_filename)
        
        # Save the HTML file
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.info(f"Story saved: {html_filename}")
        
        # Update request status and move to processed folder
        request_data['status'] = 'completed'
        request_data['completed_at'] = datetime.now().isoformat()
        request_data['output_file'] = html_filename
        if audio_path:
            request_data['audio_file'] = audio_path
        
        processed_path = os.path.join(PROCESSED_FOLDER, request_file)
        with open(processed_path, 'w') as f:
            json.dump(request_data, f, indent=2)
        
        # Remove from queue
        os.remove(request_path)
        
        return True
        
    except Exception as e:
        logger.error(f"Error processing request {request_id}: {e}")
        
        # Move to error folder
        try:
            error_path = os.path.join(ERROR_FOLDER, request_file)
            os.rename(request_path, error_path)
            
            # Update request with error info
            with open(error_path, 'r') as f:
                error_data = json.load(f)
            
            error_data['status'] = 'error'
            error_data['error'] = str(e)
            error_data['error_time'] = datetime.now().isoformat()
            
            with open(error_path, 'w') as f:
                json.dump(error_data, f, indent=2)
                
        except Exception as move_error:
            logger.error(f"Error moving failed request to error folder: {move_error}")
        
        return False
# Main loop to monitor the queue folder
def monitor_queue():
    logger.info(f"Starting story processor. Monitoring {QUEUE_FOLDER} every {CHECK_INTERVAL} seconds")
    
    while True:
        try:
            # Get list of JSON files in queue folder
            queue_files = [f for f in os.listdir(QUEUE_FOLDER) if f.endswith('.json')]
            
            if queue_files:
                logger.info(f"Found {len(queue_files)} requests in queue")
                
                for request_file in queue_files:
                    process_request(request_file)
            
            # Wait before checking again
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received. Shutting down.")
            break
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(CHECK_INTERVAL)  # Wait before retrying

if __name__ == "__main__":
    monitor_queue()