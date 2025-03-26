# Technical Context

## Technology Stack

StoryMagic is built using a combination of modern web technologies and AI services:

### Backend
- **Python**: Primary programming language
- **Flask**: Web framework for handling HTTP requests and rendering templates
- **Jinja2**: Template engine for HTML generation
- **OpenRouter**: API gateway for accessing multiple AI providers
- **OpenAI API**: Used for text-to-speech audio generation

### Frontend
- **HTML5**: Markup language for web pages
- **CSS3**: Styling for web pages
- **JavaScript**: Client-side scripting for interactive features
- **Bootstrap**: CSS framework for responsive design (implied from class names)

### Data Storage
- **File System**: JSON files for story data, configuration, and queue management
- **Environment Variables**: For sensitive configuration (API keys)

### AI Providers (via OpenRouter)
- **OpenAI**: GPT-3.5-Turbo, O1-mini, O3-mini, GPT-4o-mini
- **Anthropic**: Claude-3.5-Haiku models
- **Mistral AI**: Mistral-Saba, Mistral-Large, Mistral-Small

## Development Environment

### Requirements
- Python 3.x
- Flask and related packages
- Access to OpenRouter API
- Access to OpenAI API (for TTS)
- Environment variables for API keys

### Configuration Files
- **config.ini**: Application configuration
- **child_storyteller_mcp.json**: Model Control Protocol configuration
- **.env**: Environment variables for API keys and secrets

### Directory Structure
The application follows a standard Flask project structure with additional directories for queue management and story storage.

## API Integrations

### OpenRouter API
- **Purpose**: Access multiple AI providers through a single API
- **Authentication**: API key in request headers
- **Endpoint**: https://openrouter.ai/api/v1/chat/completions
- **Request Format**: JSON payload with model, messages, and parameters
- **Response Format**: JSON with generated content and usage statistics

### OpenAI Text-to-Speech API
- **Purpose**: Generate audio narration for stories
- **Authentication**: API key in client initialization
- **Model**: tts-1
- **Voice Selection**: Based on story language
- **Handling Long Text**: Chunking for texts exceeding 4000 characters

## Configuration System

### Environment Variables
- **OPENAI_API_KEY**: For OpenAI API access
- **OPENROUTER_API_KEY**: For OpenRouter API access
- **ANTHROPIC_API_KEY**: For direct Anthropic API access
- **DEEPSEEK_API_KEY**: For DeepSeek API access
- **ADMIN_USERNAME**: Admin dashboard username
- **ADMIN_PASSWORD**: Admin dashboard password
- **FLASK_SECRET_KEY**: For session management

### Config.ini
- **Paths**: Directories for queue, output, processed, errors, audio
- **App**: Application settings like check interval and secret key

### Model Control Protocol (MCP)
The MCP file (child_storyteller_mcp.json) defines the behavior of the AI models and the story generation process:

- **Themes**: Available story themes and their descriptions
- **Lessons**: Educational lessons to incorporate into stories
- **AI Providers**: Available AI providers and their models
- **Token Lengths**: Token limits for different story lengths
- **System Prompt**: Base instructions for AI models
- **Story Structure**: Guidelines for story structure
- **User Template**: Template for user messages to AI

## Deployment Architecture

The application is designed to run as two separate processes:

1. **Web Application (app.py)**:
   - Handles HTTP requests
   - Renders templates
   - Manages user sessions
   - Serves static files
   - Provides admin interface

2. **Story Processor (story_processor.py)**:
   - Runs as a background process
   - Monitors the queue folder for new requests
   - Processes story generation requests
   - Generates audio when requested
   - Formats and saves stories
   - Handles errors and logging
3. **Admin Processor (admin.py)**:
   - Runs as a background process
   - On port 8081
## Security Considerations

### Authentication
- Admin dashboard protected by username/password
- API keys stored in environment variables

### Input Validation
- Form validation for story creation parameters
- Security checks on file paths to prevent directory traversal

### Error Handling
- Structured error handling and logging
- Error records stored in dedicated folder

## Logging System

- **Application Log**: General application events (logs/app.log)
- **Processor Log**: Story processing events (logs/processor.log)
- **Prompt Logs**: Detailed logs of AI requests and responses (logs/prompts/)
- **Error Records**: JSON files with error details (errors/)

## Performance Considerations

### Story Generation
- Asynchronous processing to avoid blocking web requests
- Queue-based architecture for handling multiple requests
- Background processor for CPU-intensive tasks

### Audio Generation
- Chunking for long texts to handle API limitations
- Combining audio segments for seamless playback

### Resource Management
- File system monitoring for disk space
- Process monitoring for processor status
- Error handling for API failures

## Maintenance Tools

### Admin Dashboard
- Configuration management (viewing, editing, backing up)
- Backup and restore functionality

### Scripts
- **start.sh**: Start the web application and processor
- **stop.sh**: Stop the web application and processor
- **create_story_test.sh**: Test script for story creation
