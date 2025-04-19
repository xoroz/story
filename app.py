import os
from flask import Flask, request, session, g
from flask_wtf.csrf import CSRFProtect
from flask_babel import Babel

from config_loader import load_config
from auth import auth_bp, get_user_info
from routes.main_routes import main_bp
from routes.story_routes import story_bp
from routes.api_routes import api_bp
from utils.file_utils import ensure_directories_exist
from utils.logging_config import get_logger

# Get logger for this component
logger = get_logger("app")

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

# Configure supported languages
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_SUPPORTED_LOCALES'] = ['en', 'es', 'pt', 'it']

# Define locale selector function
def get_locale():
    # If language is set in session (for non-logged in users)
    if 'language' in session:
        g.locale = session['language']
        return session['language']
    
    # If user is logged in, use their preferred language
    if 'user_id' in session:
        user_info = get_user_info(session['user_id'])
        if user_info and 'preferred_language' in user_info:
            g.locale = user_info['preferred_language']
            return user_info['preferred_language']
    
    # Otherwise, try to detect from browser settings
    locale = request.accept_languages.best_match(app.config['BABEL_SUPPORTED_LOCALES'])
    g.locale = locale
    return locale

# Initialize Flask-Babel with locale selector
babel = Babel(app, locale_selector=get_locale)

# Register blueprints with appropriate URL prefixes
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(main_bp)  # No prefix for main routes
app.register_blueprint(story_bp)  # No prefix for story routes
app.register_blueprint(api_bp, url_prefix='/api')

if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True, port=8000, host='0.0.0.0')
