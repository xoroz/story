import os
import json
import time
import sys
import traceback
import openai
import logging
import anthropic
from datetime import datetime

import requests
from config_loader import load_config
from auth import add_user_story

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

# Load configuration
config = load_config()

# Get API keys from .env (already loaded by load_config)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
# Get your OpenRouter API key
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

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

def load_mcp():
    """
    Load the Model Control Protocol (MCP) JSON file.
    Fails with an error if the file is not found.
    """
    mcp_path = 'child_storyteller_mcp.json'
    
    if not os.path.exists(mcp_path):
        logger.error(f"MCP file not found at {mcp_path}")
        logger.error("The application requires this file to control AI behavior.")
        sys.exit(1)
        
    with open(mcp_path, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in MCP file: {e}")
            sys.exit(1)

def get_language_name(language_code):
    """Convert language code to language name"""
    language_map = {
        'en': 'English',
        'pt-br': 'Portuguese',
        'pt': 'Portuguese',
        'it': 'Italian',
        'es': 'Spanish'
    }
    return language_map.get(language_code, 'English')


    """Generate a story using Anthropic's Claude API"""
    # Get parameters and prompts
    params = request_data['parameters']
    prompts = request_data['prompts']
    
    # Use the prompts from the request data
    system_prompt = prompts['system_prompt']
    user_message = prompts['user_message']
    ai_model = params['ai_model']
    
    # Get API key from environment
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    
    # Check if API key is available
    if not ANTHROPIC_API_KEY:
        raise Exception("No Anthropic API key found")
    
    try:
        # Initialize the client
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        
        # Create the message
        response = client.messages.create(
            model=ai_model,
            system=system_prompt,
            max_tokens=3000,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        
        # Extract the story content from the response
        return response.content[0].text
        
    except Exception as e:
        logger.error(f"Error generating story with Claude: {e}")
        raise
def generate_story_openrouter(request_data):
    """Generate a story using OpenRouter - works with any AI provider"""
    # Get parameters and prompts
    params = request_data['parameters']
    prompts = request_data['prompts']
    request_id = request_data.get('request_id', 'unknown')
    
    # Extract parameters
    system_prompt = prompts['system_prompt']
    user_message = prompts['user_message']
    model = params['ai_model']  # Full model ID, e.g. "openai/gpt-4"
    
    # Check if API key is available
    if not OPENROUTER_API_KEY:
        raise Exception("No OpenRouter API key found")
    
    # Build OpenRouter API request
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://storymagic.app",  # Replace with your domain
        "X-Title": "StoryMagic App",  # Identify your app to OpenRouter
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7,
        "max_tokens": 3000
    }
    
    # Create log directory if it doesn't exist
    prompt_log_dir = os.path.join("logs", "prompts")
    os.makedirs(prompt_log_dir, exist_ok=True)
    
    # Create log filename for the request
    prompt_log_file = os.path.join(prompt_log_dir, f"{request_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    # Initialize log dictionary
    request_log = {
        "request_id": request_id,
        "timestamp": datetime.now().isoformat(),
        "model": model,
        "headers": {k: v for k, v in headers.items() if k != "Authorization"},  # Don't log the API key
        "payload": payload,
        "prompt_tokens_estimate": len(system_prompt) + len(user_message)  # Rough estimate
    }
    
    try:
        # Log the request before sending
        logger.info(f"Sending request to OpenRouter: {model} for request {request_id}")
        logger.debug(f"System prompt: {system_prompt[:100]}...")
        logger.debug(f"User message: {user_message[:100]}...")
        
        # Record start time
        start_time = time.time()
        
        # Make the API request
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )
        
        # Record end time
        end_time = time.time()
        response_time = end_time - start_time
        
        # Raise an exception for HTTP errors
        response.raise_for_status()
        
        # Parse the response
        data = response.json()
        
        # Extract the generated content
        content = data['choices'][0]['message']['content']
        
        # Get token usage
        usage = data.get('usage', {})
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
        total_tokens = usage.get('total_tokens', 0)
        
        # Log which model actually responded
        used_model = data.get('model', model)
        
        # Update the log with response details
        request_log.update({
            "response_time_seconds": response_time,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "used_model": used_model,
            "success": True,
            "response_length": len(content),
            "response_first_100chars": content[:100] + "..." if len(content) > 100 else content
        })
        
        logger.info(f"Story generated using model: {used_model} in {response_time:.2f} seconds")
        logger.info(f"Tokens: {prompt_tokens} prompt + {completion_tokens} completion = {total_tokens} total")
        
        # Save the complete log
        with open(prompt_log_file, 'w', encoding='utf-8') as f:
            json.dump(request_log, f, indent=2)
        
        return content
        
    except Exception as e:
        # Log the error
        error_time = time.time() - start_time if 'start_time' in locals() else 0
        
        request_log.update({
            "success": False,
            "error": str(e),
            "response_time_seconds": error_time
        })
        
        logger.error(f"Error generating story with OpenRouter after {error_time:.2f}s: {e}")
        
        # Save the error log
        with open(prompt_log_file, 'w', encoding='utf-8') as f:
            json.dump(request_log, f, indent=2)
        
        raise
    except Exception as e:
        # Log the error
        error_time = time.time() - start_time if 'start_time' in locals() else 0
        
        request_log.update({
            "success": False,
            "error": str(e),
            "response_time_seconds": error_time
        })
        
        logger.error(f"Error generating story with OpenRouter after {error_time:.2f}s: {e}")
        
        # Save the error log
        with open(prompt_log_file, 'w', encoding='utf-8') as f:
            json.dump(request_log, f, indent=2)
        
        # Provide a fallback response instead of raising the exception
        fallback_message = f"""
        Once upon a time, there was an attempt to create a magical story about {params.get('theme', 'adventure')}.
        
        Unfortunately, the magic storyteller encountered a problem: {str(e)}
        
        Please try again later, or with a different magical helper.
        """
        
        return fallback_message

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
        
        # Check if text exceeds OpenAI's 4096 character limit
        if len(text) <= 4000:  # Using 4000 to be safe
            # Call OpenAI TTS API for the entire text
            response = openai.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text
            )
            
            # Save the audio file
            response.stream_to_file(audio_path)
            
            logger.info(f"Audio generated: {audio_filename}")
            return f"audio/{audio_filename}"
        else:
            logger.info(f"Text exceeds 4096 character limit. Splitting into chunks for request {request_id}")
            
            # Split text into chunks (at paragraph boundaries if possible)
            chunks = []
            paragraphs = text.split('\n\n')
            current_chunk = ""
            
            for paragraph in paragraphs:
                # If adding this paragraph would exceed the limit, start a new chunk
                if len(current_chunk) + len(paragraph) + 2 > 4000:  # +2 for the newlines
                    if current_chunk:  # Don't add empty chunks
                        chunks.append(current_chunk)
                    current_chunk = paragraph
                else:
                    if current_chunk:
                        current_chunk += '\n\n' + paragraph
                    else:
                        current_chunk = paragraph
            
            # Add the last chunk if it's not empty
            if current_chunk:
                chunks.append(current_chunk)
            
            # If we still have chunks that are too long, split them further
            final_chunks = []
            for chunk in chunks:
                if len(chunk) <= 4000:
                    final_chunks.append(chunk)
                else:
                    # Split at sentence boundaries
                    sentences = chunk.replace('. ', '.|').replace('! ', '!|').replace('? ', '?|').split('|')
                    current_chunk = ""
                    
                    for sentence in sentences:
                        if len(current_chunk) + len(sentence) + 1 > 4000:  # +1 for the space
                            if current_chunk:
                                final_chunks.append(current_chunk)
                            current_chunk = sentence
                        else:
                            if current_chunk:
                                current_chunk += ' ' + sentence
                            else:
                                current_chunk = sentence
                    
                    if current_chunk:
                        final_chunks.append(current_chunk)
            
            logger.info(f"Split text into {len(final_chunks)} chunks for audio generation")
            
            # Process each chunk and combine the audio files
            import pydub
            from pydub import AudioSegment
            
            combined_audio = None
            temp_files = []
            
            for i, chunk in enumerate(final_chunks):
                # Generate a temporary filename for this chunk
                temp_filename = f"{request_id}_chunk_{i}.mp3"
                temp_path = os.path.join(audio_dir, temp_filename)
                temp_files.append(temp_path)
                
                # Generate audio for this chunk
                try:
                    chunk_response = openai.audio.speech.create(
                        model="tts-1",
                        voice=voice,
                        input=chunk
                    )
                    
                    # Save the chunk audio file
                    chunk_response.stream_to_file(temp_path)
                    logger.info(f"Generated audio chunk {i+1}/{len(final_chunks)}")
                    
                    # Add to combined audio
                    if combined_audio is None:
                        combined_audio = AudioSegment.from_mp3(temp_path)
                    else:
                        chunk_audio = AudioSegment.from_mp3(temp_path)
                        combined_audio += chunk_audio
                        
                except Exception as chunk_error:
                    logger.error(f"Error generating audio for chunk {i+1}: {chunk_error}")
            
            # Save the combined audio file
            if combined_audio:
                combined_audio.export(audio_path, format="mp3")
                logger.info(f"Combined audio saved to {audio_filename}")
                
                # Clean up temporary files
                for temp_file in temp_files:
                    try:
                        os.remove(temp_file)
                    except Exception as cleanup_error:
                        logger.warning(f"Could not remove temporary file {temp_file}: {cleanup_error}")
                
                return f"audio/{audio_filename}"
            else:
                logger.error("Failed to generate any audio chunks")
                return None
        
    except Exception as e:
        logger.error(f"Error generating audio: {e}")
        return None

def story_to_html(story, title, request_id, audio_path, language='en', backend='openai', model='gpt-3.5-turbo', story_about=None, username=None):
    """
    Convert a story to an HTML document
    """
    paragraphs = story.split('\n\n')
    html_paragraphs = [f"<p>{p}</p>" for p in paragraphs if p.strip()]
    
    # Format the AI provider name to look nicer
    provider_display = {
        'openai': 'OpenAI',
        'deepseek': 'DeepSeek',
        'anthropic': 'Claude',
        'mistral': 'Mistral AI'
    }.get(backend, backend.title())
    
    # Current date
    current_date = datetime.now().strftime('%B %d, %Y')
    
    # Add story_about section (if provided)
    story_about_html = ""
    if story_about:
        story_about_html = f"""
        <div class="story-brief">
            <h3>Story Brief</h3>
            <p class="story-about">{story_about}</p>
        </div>
        """
    
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
    
    # Add username info if provided
    username_html = ""
    if username:
        username_html = f"""
        <div class="story-author">
            <span class="author-label">Created by:</span>
            <span class="author-name">{username}</span>
        </div>
        """
    
    # Create HTML with links to static CSS
    html = f"""
    <!DOCTYPE html>
    <html lang="{language}">
    <head>
        <title>{title}</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="/static/css/base.css">
        <link rel="stylesheet" href="/static/css/story.css">
    </head>
    <body>
        <header class="site-header">
            <div class="container">
                <div class="logo">
                    <a href="/">StoryMagic</a>
                </div>
                <nav class="main-nav">
                    <ul>
                        <li><a href="/">Home</a></li>
                        <li><a href="/create">Create Story</a></li>
                        <li><a href="/stories">View Stories</a></li>
                    </ul>
                </nav>
            </div>
        </header>

        <main class="site-content">
            <div class="container">
                <div class="story-container">
                    <h1>{title}</h1>
                    {username_html}
                    {story_about_html}
                    <div class="story-content">
                        {"".join(html_paragraphs)}
                    </div>
                    {audio_html}
                    <div class="story-footer">
                        <div class="story-date">{current_date}</div>
                        <div class="ai-info">Created by {provider_display} using {model}</div>
                    </div>
                    <div class="story-actions">
                        <a href="/" class="btn btn-primary">Create Another Story</a>
                        <a href="/stories" class="btn btn-accent">View All Stories</a>
                    </div>
                </div>
            </div>
        </main>

        <footer class="site-footer">
            <div class="container">
                <div class="footer-content">
                    <div class="footer-info">
                        <p>StoryMagic - AI-Powered Stories for Little Imaginations</p>
                        <p>&copy; 2025 StoryMagic</p>
                    </div>
                </div>
            </div>
        </footer>
        
        <script src="/static/js/base.js"></script>
    </body>
    </html>
    """
    
    return html

def process_request(request_path):
    """
    Process a story generation request from the queue using OpenRouter
    for all AI models regardless of provider
    """
    request_file = os.path.basename(request_path)
    request_id = request_file.split('.')[0]
    process_start_time = time.time()
    
    try:
        # Read the request
        with open(request_path, 'r') as f:
            request_data = json.load(f)
        
        # Add request_id to request_data if not already present
        if 'request_id' not in request_data:
            request_data['request_id'] = request_id
        
        # Extract model info for logging
        model = request_data['parameters']['ai_model']
        logger.info(f"Processing request {request_id} - Generating story using model {model}")
        
        # Generate story using OpenRouter
        story_start_time = time.time()
        story = generate_story_openrouter(request_data)
        story_time = time.time() - story_start_time
        
        # Get story parameters
        params = request_data['parameters']
        title = params['title']
        language = params.get('language', 'en')
        enable_audio = params.get('enable_audio', False)
        
        # Generate audio if requested
        audio_path = None
        audio_time = 0
        if enable_audio:
            logger.info(f"Generating audio for request {request_id}")
            audio_start_time = time.time()
            audio_path = generate_audio(story, language, request_id)
            audio_time = time.time() - audio_start_time
        
        # Extract model information for HTML
        model_full = model  # e.g., "openai/gpt-4"
        
        # Parse provider and model name from the full model string
        if '/' in model_full:
            provider, model_name = model_full.split('/', 1)
        else:
            # Fallback if model string doesn't contain a provider prefix
            provider = "unknown"
            model_name = model_full
            
        # Format provider name for display
        provider_display = {
            'openai': 'OpenAI',
            'anthropic': 'Claude',
            'mistral': 'Mistral AI',
            'google': 'Google',
            'meta': 'Meta AI'
        }.get(provider, provider.title())
        
        # Get username if available
        username = request_data.get('username', None)
        
        # Convert to HTML - pass provider, model, and username info
        html_start_time = time.time()
        html = story_to_html(
            story=story, 
            title=title, 
            request_id=request_id, 
            audio_path=audio_path, 
            language=language,
            backend=provider_display,
            model=model_name,
            story_about=params.get('story_about', None),
            username=username
        )
        html_time = time.time() - html_start_time
        
        # Create filename for the story
        safe_title = title.lower().replace(' ', '-')
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        html_filename = f"{safe_title}_{timestamp}.html"
        html_path = os.path.join(OUTPUT_FOLDER, html_filename)
        
        # Save the story
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
            
        # Associate the story with the user if user_id is present
        if 'user_id' in request_data:
            try:
                user_id = request_data['user_id']
                add_user_story(user_id, html_filename)
                logger.info(f"Associated story {html_filename} with user {user_id}")
            except Exception as user_error:
                logger.error(f"Error associating story with user: {user_error}")
        
        # Calculate total processing time
        process_total_time = time.time() - process_start_time
        
        # Update request data with completion and timing info
        request_data['status'] = 'completed'
        request_data['completed_at'] = datetime.now().isoformat()
        request_data['output_file'] = html_filename
        if audio_path:
            request_data['audio_file'] = os.path.basename(audio_path)
        
        # Include AI info and timing data in the processed data
        request_data['ai_info'] = {
            'provider': provider_display,
            'model': model_name,
            'full_model_id': model_full
        }
        request_data['timing'] = {
            'story_generation_seconds': story_time,
            'audio_generation_seconds': audio_time,
            'html_generation_seconds': html_time,
            'total_processing_seconds': process_total_time
        }
        
        # Move to processed folder
        processed_path = os.path.join(PROCESSED_FOLDER, f"{request_id}.json")
        with open(processed_path, 'w', encoding='utf-8') as f:
            json.dump(request_data, f, indent=2)
        
        # Remove from queue
        os.remove(request_path)
        
        logger.info(f"Successfully processed request {request_id} in {process_total_time:.2f} seconds")
        logger.info(f"  Story generation: {story_time:.2f}s, Audio: {audio_time:.2f}s, HTML: {html_time:.2f}s")
        
    except Exception as e:
        # Calculate error processing time
        process_error_time = time.time() - process_start_time
        
        logger.error(f"Error processing request {request_id} after {process_error_time:.2f}s: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Create error record with timing info
        error_data = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc(),
            "processing_time_seconds": process_error_time
        }
        
        # Try to read original request data
        try:
            with open(request_path, 'r') as f:
                original_request = json.load(f)
            error_data['original_request'] = original_request
        except Exception as read_error:
            logger.error(f"Could not read original request: {read_error}")
            error_data['read_original_error'] = str(read_error)
        
        # Save error
        error_path = os.path.join(ERROR_FOLDER, f"{request_id}.json")
        with open(error_path, 'w', encoding='utf-8') as f:
            json.dump(error_data, f, indent=2)
        
        # Remove from queue
        try:
            os.remove(request_path)
        except Exception as remove_error:
            logger.error(f"Could not remove request from queue: {remove_error}")
def main():
    """
    Main function to monitor the queue and process requests
    """
    logger.info("Story Processor started")
    
    while True:
        try:
            # Get list of request files
            queue_files = [f for f in os.listdir(QUEUE_FOLDER) if f.endswith('.json')]
            
            if queue_files:
                # Process the oldest request first (sort by creation time)
                queue_files.sort(key=lambda f: os.path.getctime(os.path.join(QUEUE_FOLDER, f)))
                next_file = queue_files[0]
                
                # Process the request
                logger.info(f"Processing request: {next_file}")
                process_request(os.path.join(QUEUE_FOLDER, next_file))
            else:
                # No requests, sleep
                time.sleep(2)
                
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
            time.sleep(5)  # Sleep longer on error
            
        # Sleep between checks
        time.sleep(0.5)

if __name__ == "__main__":
    main()
