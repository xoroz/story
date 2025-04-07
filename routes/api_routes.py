from flask import Blueprint, request, jsonify
from flask_wtf.csrf import CSRFProtect
import os

from services.story_service import rate_story
from config_loader import load_config

# Create a Blueprint for API routes
api_bp = Blueprint('api', __name__)

# Load configuration
config = load_config()
OUTPUT_FOLDER = config['Paths']['output_folder']

@api_bp.route('/rate-story', methods=['POST'])
def rate_story_route():
    """Handle story rating submissions via AJAX"""
    # Get form data
    filename = request.form.get('filename')
    rating = request.form.get('rating')
    
    # Validate input
    if not filename or not rating:
        return jsonify({'success': False, 'message': 'Missing required parameters'}), 400
    
    # Security check to prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        return jsonify({'success': False, 'message': 'Invalid filename'}), 400
    
    # Check if the story exists
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'message': 'Story not found'}), 404
    
    # Add the rating
    success, message, avg_rating, rating_count = rate_story(filename, rating)
    
    if not success:
        return jsonify({'success': False, 'message': message}), 400
    
    # Return success response with updated info
    return jsonify({
        'success': True,
        'message': message,
        'average_rating': avg_rating,
        'rating_count': rating_count
    })
