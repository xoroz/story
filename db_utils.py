import os
import json
import sqlite3
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("db_utils.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DBUtils")

def get_db_connection():
    """Get a connection to the SQLite database with row factory"""
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def populate_story_db(json_path, force=False):
    """
    Populate the user_stories table with data from a processed JSON file
    
    Args:
        json_path: Path to the processed JSON file
        force: If True, will attempt to process even if user_id is missing
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Read the JSON file
        with open(json_path, 'r', encoding='utf-8') as f:
            story_data = json.load(f)
        
        # Extract the necessary data
        request_id = story_data.get('request_id', 'unknown')
        user_id = story_data.get('user_id')
        
        # If no user_id, we can't associate with a user unless force is True
        if not user_id:
            if force:
                # Use a default user_id of 1 (typically admin)
                user_id = 1
                logger.warning(f"No user_id found in {json_path}, using default user_id=1")
            else:
                logger.warning(f"No user_id found in {json_path}, skipping DB update")
                return False
        
        # Extract parameters
        params = story_data.get('parameters', {})
        title = params.get('title', 'Untitled')
        theme = params.get('theme', '')
        theme_description = params.get('theme_description', '')
        language = params.get('language', 'en')
        age_range = params.get('age_range', '')
        lesson = params.get('lesson', '')
        characters = params.get('characters', '')
        story_about = params.get('story_about', '')
        ai_model = params.get('ai_model', '')
        
        # Extract AI info
        ai_info = story_data.get('ai_info', {})
        provider = ai_info.get('provider', '')
        
        # Extract output files
        output_file = story_data.get('output_file', '')
        audio_file = story_data.get('audio_file', '')
        
        # Extract timing info
        timing = story_data.get('timing', {})
        processing_time = timing.get('total_processing_seconds', 0)
        
        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get table info to check available columns
        cursor.execute("PRAGMA table_info(user_stories)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Check if this story already exists in the database
        existing = cursor.execute(
            'SELECT id FROM user_stories WHERE story_filename = ?', 
            (output_file,)
        ).fetchone()
        
        if existing:
            # Build dynamic update query based on available columns
            update_fields = []
            update_values = []
            
            # Map of field names to values
            field_map = {
                'title': title,
                'theme': theme,
                'theme_description': theme_description,
                'language': language,
                'age_range': age_range,
                'lesson': lesson,
                'characters': characters,
                'story_about': story_about,
                'ai_model': ai_model,
                'provider': provider,
                'output_file': output_file,
                'audio_file': audio_file,
                'processing_time': processing_time
            }
            
            # Add fields that exist in the table
            for field, value in field_map.items():
                if field in columns:
                    update_fields.append(f"{field} = ?")
                    update_values.append(value)
            
            # Add the WHERE clause value
            update_values.append(output_file)
            
            # Execute the update if we have fields to update
            if update_fields:
                update_query = f'''
                UPDATE user_stories SET
                    {', '.join(update_fields)}
                WHERE story_filename = ?
                '''
                cursor.execute(update_query, update_values)
                logger.info(f"Updated existing story record for {output_file}")
            else:
                logger.warning(f"No fields to update for {output_file}")
        else:
            # Build dynamic insert query based on available columns
            insert_fields = ['user_id', 'story_filename']
            insert_values = [user_id, output_file]
            
            # Map of field names to values
            field_map = {
                'title': title,
                'theme': theme,
                'theme_description': theme_description,
                'language': language,
                'age_range': age_range,
                'lesson': lesson,
                'characters': characters,
                'story_about': story_about,
                'ai_model': ai_model,
                'provider': provider,
                'output_file': output_file,
                'audio_file': audio_file,
                'processing_time': processing_time
            }
            
            # Add fields that exist in the table
            for field, value in field_map.items():
                if field in columns:
                    insert_fields.append(field)
                    insert_values.append(value)
            
            # Execute the insert
            placeholders = ', '.join(['?' for _ in insert_fields])
            insert_query = f'''
            INSERT INTO user_stories (
                {', '.join(insert_fields)}
            ) VALUES ({placeholders})
            '''
            cursor.execute(insert_query, insert_values)
            logger.info(f"Inserted new story record for {output_file}")
        
        # Commit and close
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error populating database from {json_path}: {str(e)}")
        return False

def get_stories_for_user(user_id, limit=None):
    """
    Get all stories for a specific user
    
    Args:
        user_id: The user ID
        limit: Optional limit on number of stories to return
    
    Returns:
        list: List of story dictionaries
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if is_private column exists
        cursor.execute("PRAGMA table_info(user_stories)")
        columns = [column[1] for column in cursor.fetchall()]
        
        query = '''
        SELECT * FROM user_stories 
        WHERE user_id = ? 
        ORDER BY created_at DESC
        '''
        
        if limit:
            query += f' LIMIT {int(limit)}'
        
        stories = cursor.execute(query, (user_id,)).fetchall()
        
        # Convert to list of dictionaries
        story_list = []
        for story in stories:
            story_dict = dict(story)
            
            # Add is_private field if it doesn't exist in the database
            if 'is_private' not in story_dict and 'is_private' not in columns:
                # Default to user's global privacy setting
                user = cursor.execute('SELECT private FROM users WHERE id = ?', (user_id,)).fetchone()
                story_dict['is_private'] = bool(user['private']) if user else False
            elif 'is_private' in story_dict:
                # Convert to boolean
                story_dict['is_private'] = bool(story_dict['is_private'])
            
            # Check if the story file still exists
            story_filename = story_dict.get('story_filename')
            if story_filename:
                # Get the output folder from config
                from config_loader import load_config
                config = load_config()
                output_folder = config['Paths']['output_folder']
                
                # Check if the file exists
                story_path = os.path.join(output_folder, story_filename)
                if os.path.exists(story_path):
                    story_list.append(story_dict)
                else:
                    # Story file doesn't exist, delete from database
                    logger.info(f"Story file {story_filename} not found, removing from database")
                    cursor.execute('DELETE FROM user_stories WHERE id = ?', (story_dict['id'],))
                    conn.commit()
            else:
                # No filename, include it anyway
                story_list.append(story_dict)
        
        conn.close()
        return story_list
        
    except Exception as e:
        logger.error(f"Error getting stories for user {user_id}: {str(e)}")
        return []

def get_all_stories(limit=None):
    """
    Get all stories in the database
    
    Args:
        limit: Optional limit on number of stories to return
    
    Returns:
        list: List of story dictionaries
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if is_private column exists
        cursor.execute("PRAGMA table_info(user_stories)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # If is_private column exists, exclude private stories
        if 'is_private' in columns:
            query = '''
            SELECT s.*, u.username 
            FROM user_stories s
            JOIN users u ON s.user_id = u.id
            WHERE s.is_private = 0
            ORDER BY s.created_at DESC
            '''
        else:
            query = '''
            SELECT s.*, u.username 
            FROM user_stories s
            JOIN users u ON s.user_id = u.id
            ORDER BY s.created_at DESC
            '''
        
        if limit:
            query += f' LIMIT {int(limit)}'
        
        stories = cursor.execute(query).fetchall()
        
        # Get the output folder from config
        from config_loader import load_config
        config = load_config()
        output_folder = config['Paths']['output_folder']
        
        # Convert to list of dictionaries and check if files exist
        story_list = []
        for story in stories:
            story_dict = dict(story)
            
            # Check if the story file still exists
            story_filename = story_dict.get('story_filename')
            if story_filename:
                # Check if the file exists
                story_path = os.path.join(output_folder, story_filename)
                if os.path.exists(story_path):
                    story_list.append(story_dict)
                else:
                    # Story file doesn't exist, delete from database
                    logger.info(f"Story file {story_filename} not found, removing from database")
                    cursor.execute('DELETE FROM user_stories WHERE id = ?', (story_dict['id'],))
                    conn.commit()
            else:
                # No filename, include it anyway
                story_list.append(story_dict)
        
        conn.close()
        return story_list
        
    except Exception as e:
        logger.error(f"Error getting all stories: {str(e)}")
        return []

def update_story_rating(story_id, rating):
    """
    Update the rating for a story
    
    Args:
        story_id: The story ID
        rating: The new rating (1-5)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get current rating
        story = cursor.execute('SELECT rating FROM user_stories WHERE id = ?', (story_id,)).fetchone()
        if not story:
            conn.close()
            return False
        
        # Update rating
        cursor.execute('UPDATE user_stories SET rating = ? WHERE id = ?', (rating, story_id))
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error updating rating for story {story_id}: {str(e)}")
        return False

def update_story_views(story_id):
    """
    Increment the view count for a story
    
    Args:
        story_id: The story ID
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update views
        cursor.execute('UPDATE user_stories SET views = views + 1 WHERE id = ?', (story_id,))
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error updating views for story {story_id}: {str(e)}")
        return False

def process_json_directory(directory_path, force=False):
    """
    Process all JSON files in a directory and populate the database
    
    Args:
        directory_path: Path to the directory containing JSON files
        force: If True, will attempt to process even if user_id is missing
    
    Returns:
        tuple: (success_count, failure_count)
    """
    success_count = 0
    failure_count = 0
    
    try:
        # Get all JSON files in the directory
        json_files = [f for f in os.listdir(directory_path) if f.endswith('.json')]
        
        for json_file in json_files:
            json_path = os.path.join(directory_path, json_file)
            
            # Process the file
            if populate_story_db(json_path, force=force):
                success_count += 1
            else:
                failure_count += 1
        
        logger.info(f"Processed {success_count + failure_count} JSON files: {success_count} successful, {failure_count} failed")
        return (success_count, failure_count)
        
    except Exception as e:
        logger.error(f"Error processing JSON directory {directory_path}: {str(e)}")
        return (success_count, failure_count)

def get_user_private_setting(user_id):
    """
    Get the private setting for a user
    
    Args:
        user_id: The user ID
    
    Returns:
        bool: True if private, False otherwise
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if private column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'private' in columns:
            result = cursor.execute('SELECT private FROM users WHERE id = ?', (user_id,)).fetchone()
            conn.close()
            
            if result and result['private'] is not None:
                return bool(result['private'])
            return False
        else:
            # If private column doesn't exist, return default value
            conn.close()
            return False
        
    except Exception as e:
        logger.error(f"Error getting private setting for user {user_id}: {str(e)}")
        return False

def update_user_private_setting(user_id, private):
    """
    Update the private setting for a user
    
    Args:
        user_id: The user ID
        private: Boolean indicating if the user's stories should be private
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if private column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'private' in columns:
            cursor.execute('UPDATE users SET private = ? WHERE id = ?', (1 if private else 0, user_id))
            conn.commit()
            conn.close()
            return True
        else:
            # If private column doesn't exist, add it first
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN private BOOLEAN DEFAULT 0")
                cursor.execute('UPDATE users SET private = ? WHERE id = ?', (1 if private else 0, user_id))
                conn.commit()
                conn.close()
                logger.info(f"Added private column to users table and updated setting for user {user_id}")
                return True
            except Exception as alter_error:
                logger.error(f"Error adding private column to users table: {str(alter_error)}")
                conn.close()
                return False
        
    except Exception as e:
        logger.error(f"Error updating private setting for user {user_id}: {str(e)}")
        return False

def update_story_privacy(story_id, is_private):
    """
    Update the privacy setting for a specific story
    
    Args:
        story_id: The story ID
        is_private: Boolean indicating if the story should be private
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if is_private column exists
        cursor.execute("PRAGMA table_info(user_stories)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'is_private' in columns:
            cursor.execute('UPDATE user_stories SET is_private = ? WHERE id = ?', 
                          (1 if is_private else 0, story_id))
            conn.commit()
            conn.close()
            return True
        else:
            # If is_private column doesn't exist, add it first
            try:
                cursor.execute("ALTER TABLE user_stories ADD COLUMN is_private BOOLEAN DEFAULT 0")
                cursor.execute('UPDATE user_stories SET is_private = ? WHERE id = ?', 
                              (1 if is_private else 0, story_id))
                conn.commit()
                conn.close()
                logger.info(f"Added is_private column to user_stories table and updated setting for story {story_id}")
                return True
            except Exception as alter_error:
                logger.error(f"Error adding is_private column to user_stories table: {str(alter_error)}")
                conn.close()
                return False
        
    except Exception as e:
        logger.error(f"Error updating privacy setting for story {story_id}: {str(e)}")
        return False

def get_story_details(story_id):
    """
    Get detailed information about a specific story
    
    Args:
        story_id: The story ID
    
    Returns:
        dict: Story details or None if not found
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        story = cursor.execute('''
            SELECT * FROM user_stories WHERE id = ?
        ''', (story_id,)).fetchone()
        
        if story:
            story_dict = dict(story)
            
            # Check if the story file still exists
            story_filename = story_dict.get('story_filename')
            if story_filename:
                # Get the output folder from config
                from config_loader import load_config
                config = load_config()
                output_folder = config['Paths']['output_folder']
                
                # Check if the file exists
                story_path = os.path.join(output_folder, story_filename)
                if not os.path.exists(story_path):
                    # Story file doesn't exist, delete from database
                    logger.info(f"Story file {story_filename} not found, removing from database")
                    cursor.execute('DELETE FROM user_stories WHERE id = ?', (story_dict['id'],))
                    conn.commit()
                    conn.close()
                    return None
            
            conn.close()
            return story_dict
        
        conn.close()
        return None
        
    except Exception as e:
        logger.error(f"Error getting story details for ID {story_id}: {str(e)}")
        return None

def get_user_auth_type(user_id):
    """
    Get the authentication type for a user
    
    Args:
        user_id: The user ID
    
    Returns:
        str: The authentication type
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if auth_type column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'auth_type' in columns:
            result = cursor.execute('SELECT auth_type FROM users WHERE id = ?', (user_id,)).fetchone()
            conn.close()
            
            if result and result['auth_type'] is not None:
                return result['auth_type']
            return 'local'
        else:
            # If auth_type column doesn't exist, return default value
            conn.close()
            return 'local'
        
    except Exception as e:
        logger.error(f"Error getting auth_type for user {user_id}: {str(e)}")
        return 'local'

def update_user_auth_type(user_id, auth_type):
    """
    Update the authentication type for a user
    
    Args:
        user_id: The user ID
        auth_type: The authentication type
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if auth_type column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'auth_type' in columns:
            cursor.execute('UPDATE users SET auth_type = ? WHERE id = ?', (auth_type, user_id))
            conn.commit()
            conn.close()
            return True
        else:
            # If auth_type column doesn't exist, add it first
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN auth_type TEXT DEFAULT 'local'")
                cursor.execute('UPDATE users SET auth_type = ? WHERE id = ?', (auth_type, user_id))
                conn.commit()
                conn.close()
                logger.info(f"Added auth_type column to users table and updated setting for user {user_id}")
                return True
            except Exception as alter_error:
                logger.error(f"Error adding auth_type column to users table: {str(alter_error)}")
                conn.close()
                return False
        
    except Exception as e:
        logger.error(f"Error updating auth_type for user {user_id}: {str(e)}")
        return False
