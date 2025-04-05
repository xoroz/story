# StoryMagic - AI-Powered Children's Story Generator

A Flask web application that generates personalized children's stories using multiple AI providers (OpenAI, Claude, Mistral AI) through the OpenRouter API.
## Context Priming
read README.md memory-bank/*  
run git ls-files to list all files

## Features

### Core Features
- Personalized story generation based on user preferences:
  - Age range (3-6, 7-9, 10-12 years)
  - Theme selection (forest, dinosaur, space, city)
  - Educational lesson (family importance, friendship, trust, love, honesty, perseverance)
  - Character descriptions
  - Story length options (short, medium, long)
  - Multiple language support (English, Spanish, Italian, Portuguese)
  - Optional audio narration
- Multiple AI providers through OpenRouter API:
  - OpenAI (GPT-3.5-Turbo, O1-mini, O3-mini, GPT-4o-mini)
  - Claude (Claude-3.5-Haiku models)
  - Mistral AI (Mistral-Saba, Mistral-Large, Mistral-Small)
- Story listing with metadata
- Story rating system
- Audio narration using OpenAI TTS

### User Features
- User registration and login system
- User profile page with credit management
- Story ownership and association with users
- Privacy controls for stories (public/private)
- Credit system for story creation

### Database Integration
- SQLite database for user and story data
- Hybrid approach maintaining file-based storage for stories
- Database schema defined in config.ini
- Automatic database updates when stories are created
- Manual database update tools for batch processing

### Admin Dashboard
- System monitoring (process status, queue status, disk usage)
- Process control (start/stop/restart web app and processor)
- Story management (view, delete)
- Configuration editing (MCP JSON and config.ini)
- Backup and restore system

## Getting Started

### Prerequisites
- Python 3.x
- API keys for OpenRouter and OpenAI (for TTS)

### Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables by creating a `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key
   OPENROUTER_API_KEY=your_openrouter_api_key
   ADMIN_USERNAME=your_admin_username (default: admin)
   ADMIN_PASSWORD=your_admin_password (default: admin123)
   ```

### Running the Application

Start all components with a single command:
```
./start.sh
```

This will start:
- Web application (port 8000)
- Story processor (background)
- Admin dashboard (port 8001)

To stop all services:
```
./stop.sh
```

### Accessing the Application
- Main application: http://localhost:8000
- Admin dashboard: http://localhost:8001 (login with configured credentials)

### Running Tests
StoryMagic includes an automated test suite using pytest and Playwright. To run the tests:

1. Install test dependencies:
   ```
   pip install -r requirements.txt
   playwright install  # Install browser binaries
   ```

2. Run all tests:
   ```
   ./test-all.sh
   ```

3. View test results:
   The HTML test report will be available at `test-results/report.html`

Test coverage includes:
- Home page functionality
- Stories listing page
- Create story form
- Admin dashboard login
- Admin functionality

## Project Structure
```
.
├── README.md
├── admin.py              # Admin dashboard server (port 8001)
├── app.py                # Main web application (port 8000)
├── auth.py               # User authentication module
├── backups/              # Backup files for config and system
├── child_storyteller_mcp.json  # Model Control Protocol configuration
├── config.ini            # Application configuration (includes DB schema)
├── config_loader.py      # Configuration loader utility
├── database.db           # SQLite database for users and stories
├── db_utils.py           # Database utility functions
├── init_db.py            # Database initialization script
├── logs/                 # Log files
│   └── prompts/          # Detailed logs of AI requests
├── memory-bank/          # Project documentation
├── pids/                 # Process ID files
├── process_stories.py    # Script to process stories into database
├── processed/            # Processed story requests
├── queue/                # Queue for story requests
├── requirements.txt      # Python dependencies
├── start.sh              # Start script for all services
├── static/               # Static assets (CSS, JS, images)
│   ├── css/
│   │   ├── admin.css
│   │   ├── auth.css      # Styles for authentication pages
│   │   ├── base.css
│   │   └── ...
│   ├── images/
│   └── js/
│       ├── auth.js       # JavaScript for authentication
│       └── ...
├── stop.sh               # Stop script for all services
├── stories/              # Generated stories in HTML
│   └── audio/            # Generated audio narration
├── story_metadata.json   # Story metadata (ratings, views)
├── story_processor.py    # Background story processing service
└── templates/            # HTML templates
    ├── admin/            # Admin dashboard templates
    ├── auth/             # Authentication templates
    │   ├── login.html
    │   ├── profile.html
    │   └── register.html
    └── ...               # Main application templates
```
