import os
from flask import Flask
from flask_wtf.csrf import CSRFProtect

from config_loader import load_config
from auth import auth_bp
from routes.main_routes import main_bp
from routes.story_routes import story_bp
from routes.api_routes import api_bp
from utils.file_utils import ensure_directories_exist

# Load configuration
config = load_config()

# Ensure directories exist
paths = ensure_directories_exist(config)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = config['App']['secret_key']

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Exempt API routes from CSRF protection
csrf.exempt(api_bp)

# Register blueprints with appropriate URL prefixes
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(main_bp)  # No prefix for main routes
app.register_blueprint(story_bp)  # No prefix for story routes
app.register_blueprint(api_bp, url_prefix='/api')

if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True, port=8000, host='0.0.0.0')
