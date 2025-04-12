import os
import re
import json
import uuid
from datetime import datetime
from flask import session, flash, redirect, url_for
from auth import get_user_info, use_credit
from utils.file_utils import get_story_metadata, save_story_metadata, load_mcp
from utils.template_utils import get_language_name
from db_utils import get_user_private_setting, get_story_private_setting, get_story_details

def create_story_request(form_data, user_id):
    """
    Create a story generation request from form data
    
    Args:
        form_data: Form data from the request
        user_id: User ID
        
    Returns:
        tuple: (request_data, request_id, error_message)
    """
    try:
        # Generate a unique request ID
        request_id = str(uuid.uuid4())
        
        # Load MCP
        mcp = load_mcp()
        
        # Get basic parameters
        theme_id = form_data.get('theme')
        age_range = form_data.get('age_range')
        length_setting = form_data.get('length', 'medium')
        language = form_data.get('language', 'en')
        lesson = form_data.get('lesson')
        characters = form_data.get('characters', '')
        story_about = form_data.get('story_about', '')
        
        # Look up theme description
        theme_map = mcp.get("themes", {})
        if theme_id not in theme_map:
            return None, None, f"Error: Selected theme '{theme_id}' not found in MCP"
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
            return None, None, "Error: User template not found in MCP"
            
        user_message = user_template.format(
            age_range=age_range,
            characters=characters,
            theme_description=theme_description,
            story_about=story_about,
            lesson=lesson,
            length=length_setting,
            tokens=max_tokens
        )
        
        # Get user information
        user_info = get_user_info(user_id)
        
        # Create request data
        request_data = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "username": user_info['username'] if user_info else "Unknown",
            "email": user_info['email'] if user_info else "unknown@example.com",
            "parameters": {
                "age_range": age_range,
                "theme": theme_id,
                "theme_description": theme_description,
                "lesson": lesson,
                "characters": characters,
                "story_about": story_about,
                "title": form_data.get('title', 'My Story'),
                "length": length_setting,
                "max_tokens": max_tokens,
                "language": language,
                "ai_model": form_data.get('ai_model', 'openai/gpt-3.5-turbo'),
                "enable_audio": form_data.get('enable_audio') == 'true',
                "is_private": form_data.get('is_private') == 'true'
            },
            "prompts": {
                "system_prompt": system_prompt,
                "user_message": user_message
            },
            "status": "pending",
            "backend": form_data.get('backend', 'openai')
        }
        
        return request_data, request_id, None
        
    except Exception as e:
        return None, None, f"Error creating story request: {str(e)}"

def save_story_request(request_data, queue_folder):
    """
    Save a story request to the queue folder
    
    Args:
        request_data: Request data dictionary
        queue_folder: Path to the queue folder
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        request_id = request_data['request_id']
        filename = f"{queue_folder}/{request_id}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(request_data, f, indent=2)
            
        return True
    except Exception as e:
        print(f"Error saving story request: {str(e)}")
        return False

def check_story_status(request_id, queue_folder, processed_folder, error_folder):
    """
    Check the status of a story request
    
    Args:
        request_id: Request ID
        queue_folder: Path to the queue folder
        processed_folder: Path to the processed folder
        error_folder: Path to the error folder
        
    Returns:
        tuple: (status, data, error_message)
            status: 'queued', 'processed', 'error', or 'not_found'
            data: Request data if found, None otherwise
            error_message: Error message if status is 'error', None otherwise
    """
    # Check if request exists in queue
    request_path = os.path.join(queue_folder, f"{request_id}.json")
    if os.path.exists(request_path):
        with open(request_path, 'r') as f:
            request_data = json.load(f)
        return 'queued', request_data, None
    
    # Check if processed
    processed_path = os.path.join(processed_folder, f"{request_id}.json")
    if os.path.exists(processed_path):
        with open(processed_path, 'r') as f:
            request_data = json.load(f)
        return 'processed', request_data, None
    
    # Check if error
    error_path = os.path.join(error_folder, f"{request_id}.json")
    if os.path.exists(error_path):
        with open(error_path, 'r') as f:
            request_data = json.load(f)
        return 'error', request_data, request_data.get('error', 'Unknown error')
    
    # Not found
    return 'not_found', None, None

def get_story_content(filename, output_folder):
    """
    Get the content of a story file
    
    Args:
        filename: Story filename
        output_folder: Path to the output folder
        
    Returns:
        tuple: (content, error_message)
    """
    # Security check to prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        return None, 'Invalid story filename'
        
    file_path = os.path.join(output_folder, filename)
    if not os.path.exists(file_path):
        return None, 'Story not found'
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content, None
    except Exception as e:
        return None, f"Error reading story file: {str(e)}"

def extract_story_metadata(content, filename, processed_folder, audio_folder):
    """
    Extract metadata from a story HTML content
    
    Args:
        content: HTML content
        filename: Story filename
        processed_folder: Path to the processed folder
        audio_folder: Path to the audio folder
        
    Returns:
        dict: Story metadata
    """
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
    
    # Extract username if available
    username = None
    username_match = re.search(r'<span class="author-name">(.*?)</span>', content)
    if username_match:
        username = username_match.group(1)
    
    # Try to find request_id from HTML content
    request_id = None
    if audio_match:
        request_id = re.search(r'/audio/([a-f0-9-]+)\.mp3', audio_match.group(0))
        if request_id:
            request_id = request_id.group(1)
    
    # If we have a request_id, try to load the processed request file
    user_id = None
    if request_id:
        processed_path = os.path.join(processed_folder, f"{request_id}.json")
        if os.path.exists(processed_path):
            try:
                with open(processed_path, 'r') as f:
                    request_data = json.load(f)
                
                # Get user info
                user_id = request_data.get('user_id')
                if not username:
                    username = request_data.get('username', None)
                
                # Get additional metadata
                params = request_data.get('parameters', {})
                theme = params.get('theme', '')
                age = params.get('age_range', '')
                language_code = params.get('language', '')
                
                # Get AI model info
                ai_info = request_data.get('ai_info', {})
                if not provider_display or provider_display == 'AI':
                    provider_display = ai_info.get('provider', provider_display)
                if not model or model == 'Unknown':
                    model = ai_info.get('model', model)
                
                # Get processing time
                timing = request_data.get('timing', {})
                processing_time = timing.get('total_processing_seconds', 0)
                
                # Get audio file size if available
                audio_size = None
                audio_file = request_data.get('audio_file')
                if audio_file:
                    audio_path = os.path.join(audio_folder, audio_file)
                    if os.path.exists(audio_path):
                        audio_size = os.path.getsize(audio_path) / (1024 * 1024)  # Size in MB
                
                return {
                    'title': title,
                    'story_html': story_html,
                    'story_about': story_about,
                    'audio_path': audio_path,
                    'provider_display': provider_display,
                    'model': model,
                    'username': username,
                    'user_id': user_id,
                    'request_id': request_id,
                    'theme': theme,
                    'age': age,
                    'language_code': language_code,
                    'processing_time': processing_time,
                    'audio_size': round(audio_size, 2) if audio_size else None,
                    'has_audio': audio_size is not None,
                }
            except Exception as e:
                print(f"Error loading processed data: {e}")
    
    # Return basic metadata if we couldn't get enhanced metadata
    return {
        'title': title,
        'story_html': story_html,
        'story_about': story_about,
        'audio_path': audio_path,
        'provider_display': provider_display,
        'model': model,
        'username': username,
        'user_id': user_id,
        'request_id': request_id,
    }

def check_story_privacy(story_id, user_id, session_user_id):
    """
    Check if a story should be private based on story and user settings
    
    Args:
        story_id: Story ID
        user_id: Story owner user ID
        session_user_id: Current session user ID
        
    Returns:
        bool: True if the story should be private, False otherwise
    """
    # If no user ID, story is public
    if not user_id:
        return False
    
    # If current user is the owner, they can see it
    if user_id == session_user_id:
        return False
    
    # Check if the specific story is private
    if story_id:
        is_story_private = get_story_private_setting(story_id)
        if is_story_private:
            return True
    
    # Check if the user has set all their stories to private
    is_user_private = get_user_private_setting(user_id)
    
    return is_user_private

def update_story_view_count(filename):
    """
    Increment the view count for a story
    
    Args:
        filename: Story filename
    """
    metadata = get_story_metadata()
    if filename not in metadata['stories']:
        metadata['stories'][filename] = {
            'ratings': [],
            'views': 0
        }
    
    # Increment view count
    metadata['stories'][filename]['views'] = metadata['stories'][filename].get('views', 0) + 1
    save_story_metadata(metadata)
    
    return metadata['stories'][filename]

def rate_story(filename, rating):
    """
    Add a rating to a story
    
    Args:
        filename: Story filename
        rating: Rating value (1-5)
        
    Returns:
        tuple: (success, message, avg_rating, rating_count)
    """
    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            return False, 'Rating must be between 1 and 5', 0, 0
    except ValueError:
        return False, 'Invalid rating value', 0, 0
    
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
    
    return True, 'Rating submitted successfully!', avg_rating, len(ratings)

def get_story_list(session_user_id, output_folder, processed_folder, audio_folder):
    """
    Get a list of all stories, respecting privacy settings
    
    Args:
        session_user_id: Current session user ID (None if not logged in)
        output_folder: Path to the output folder
        processed_folder: Path to the processed folder
        audio_folder: Path to the audio folder
        
    Returns:
        list: List of story dictionaries
    """
    from db_utils import get_all_stories, get_user_private_setting
    
    # Get list of stories from database
    stories_db = get_all_stories()
    
    # Filter stories based on privacy settings
    filtered_stories = []
    
    for story in stories_db:
        user_id = story.get('user_id')
        
        # Skip if no user_id (shouldn't happen, but just in case)
        if not user_id:
            filtered_stories.append(story)
            continue
            
        # If this is the current user's story, include it
        if session_user_id and user_id == session_user_id:
            filtered_stories.append(story)
            continue
            
        # Check if the story is private
        is_story_private = story.get('is_private', 0) == 1
        
        # Check if the user has set all their stories to private
        is_user_private = get_user_private_setting(user_id)
        
        # If user is not logged in, skip any private stories
        if not session_user_id:
            # Skip if either the story or the user is private
            if is_story_private or is_user_private:
                continue
                
        # Only include the story if neither the story nor the user is private
        if not is_story_private and not is_user_private:
            filtered_stories.append(story)
    
    # Replace the database stories with our filtered list
    stories_db = filtered_stories
    
    # Get story metadata from file system
    story_files = []
    
    # Get story metadata
    metadata = get_story_metadata()
    stories_metadata = metadata.get('stories', {})
    
    for file in os.listdir(output_folder):
        if file.endswith('.html'):
            # Get creation time and simple name
            path = os.path.join(output_folder, file)
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
            theme = age = model = provider = processing_time = audio_size = language_code = username = user_id = None
            
            # If we have a request_id, try to load the processed request file
            if request_id:
                processed_path = os.path.join(processed_folder, f"{request_id}.json")
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
                        
                        # Get user info
                        user_id = request_data.get('user_id')
                        username = request_data.get('username', None)
                        
                        # Get audio file size if available
                        audio_file = request_data.get('audio_file')
                        if audio_file:
                            audio_path = os.path.join(audio_folder, audio_file)
                            if os.path.exists(audio_path):
                                audio_size = os.path.getsize(audio_path) / (1024 * 1024)  # Size in MB
                    except Exception as e:
                        # If there's an error, continue without the enhanced metadata
                        print(f"Error loading processed data for {request_id}: {e}")
            
            # Check if this story should be private
            if user_id and user_id != session_user_id:
                # Check if the story is private
                is_story_private = False
                if request_id:
                    processed_path = os.path.join(processed_folder, f"{request_id}.json")
                    if os.path.exists(processed_path):
                        try:
                            with open(processed_path, 'r') as f:
                                request_data = json.load(f)
                            # Check if the story is marked as private
                            is_story_private = request_data.get('parameters', {}).get('is_private', False)
                        except Exception:
                            pass
                
                # Check if the user has set all their stories to private
                is_user_private = get_user_private_setting(user_id)
                
                # Skip this story if either the story or the user is private
                if is_story_private or is_user_private:
                    continue
            
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
                'language': get_language_name(language_code) if language_code else None,
                'username': username,
                'user_id': user_id
            })
    
    # Sort by creation time, newest first
    story_files.sort(key=lambda x: x['created'], reverse=True)
    
    return story_files

def get_prefill_data_for_story(story_id):
    """
    Get prefill data for recreating a story
    
    Args:
        story_id: Story ID
        
    Returns:
        dict: Prefill data for the create story form
    """
    # Get story details from database
    story_details = get_story_details(story_id)
    
    if not story_details:
        return None
    
    # Create prefill data for the create story form
    prefill_data = {
        'title': story_details.get('title', ''),
        'theme': story_details.get('theme', ''),
        'age_range': story_details.get('age_range', '10-12'),
        'lesson': story_details.get('lesson', ''),
        'characters': story_details.get('characters', ''),
        'story_about': story_details.get('story_about', ''),
        'language': story_details.get('language', 'en'),
        'ai_model': story_details.get('ai_model', ''),
        'provider': story_details.get('provider', 'openai')
    }
    
    return prefill_data
