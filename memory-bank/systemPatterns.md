# System Patterns

## Architecture Overview

StoryMagic follows a modular architecture with clear separation of concerns between the web application, background processing, and administration components. The system is designed around a queue-based processing model to handle potentially long-running story generation tasks asynchronously.

```mermaid
flowchart TD
    User[User] --> WebApp[Flask Web Application]
    WebApp --> Queue[Story Queue]
    Queue --> Processor[Story Processor]
    Processor --> AI[AI Providers]
    AI --> Processor
    Processor --> Output[Story Output]
    Output --> WebApp
    Admin[Administrator] --> AdminDashboard[Admin Dashboard]
    AdminDashboard --> WebApp
    AdminDashboard --> Processor
```

## Core Components

### 1. Web Application (app.py)
- **Responsibility**: Handle HTTP requests, render templates, manage user sessions
- **Key Features**:
  - Story creation form handling
  - Story viewing and listing
  - Story rating system
  - Admin authentication
  - Static file serving

### 2. Story Processor (story_processor.py)
- **Responsibility**: Process story generation requests from the queue
- **Key Features**:
  - Continuous monitoring of the queue folder
  - AI provider integration via OpenRouter
  - Audio generation using OpenAI's TTS API
  - HTML formatting of generated stories
  - Error handling and logging

### 3. Admin Dashboard (admin.py)
- **Responsibility**: System monitoring and management
- **Key Features**:
  - Story management
  - Configuration management
  - Backup and restore functionality

### 4. Model Control Protocol (MCP)
- **Responsibility**: Define AI behavior and system configuration
- **Key Features**:
  - AI provider and model definitions
  - Theme and lesson definitions
  - System prompts and templates
  - Token length settings

## Data Flow

### Story Creation Flow
1. User submits story creation form
2. Web application validates input and creates a request JSON file
3. Request file is placed in the queue folder
4. User is redirected to waiting page that polls for completion
5. Story processor picks up the request from the queue
6. Processor generates story using selected AI provider via OpenRouter
7. If audio is requested, processor generates audio using OpenAI TTS
8. Processor formats story as HTML and saves to output folder
9. Processor updates request with completion info and moves to processed folder
10. Waiting page detects completion and redirects to story view

```mermaid
sequenceDiagram
    actor User
    participant WebApp as Flask Web App
    participant Queue as Queue Folder
    participant Processor as Story Processor
    participant AI as AI Provider
    participant TTS as Text-to-Speech
    participant Output as Output Folder

    User->>WebApp: Submit story request
    WebApp->>Queue: Create request JSON
    WebApp->>User: Redirect to waiting page
    loop Polling
        User->>WebApp: Check status
        WebApp->>Queue: Check if request exists
        WebApp->>Output: Check if story exists
    end
    Processor->>Queue: Pick up request
    Processor->>AI: Generate story
    AI->>Processor: Return story text
    opt Audio Enabled
        Processor->>TTS: Generate audio
        TTS->>Processor: Return audio file
    end
    Processor->>Output: Save HTML and audio
    Processor->>Queue: Remove request
    User->>WebApp: Redirect to story
    WebApp->>Output: Fetch story
    WebApp->>User: Display story
```

### Admin Dashboard Flow
1. Admin logs in with basic credentials in port 8001
4. Admin can perform various management actions
5. Actions are processed by the web application
6. Results are returned to the dashboard

## Design Patterns

### 1. Model-View-Controller (MVC)
- **Models**: JSON data structures for stories, configuration, etc.
- **Views**: Jinja2 templates for rendering HTML
- **Controllers**: Flask routes and admin blueprint

### 2. Queue-Based Processing
- Asynchronous processing of story generation requests
- File-based queue system using filesystem directories
- Status tracking through file movement between directories

### 3. Factory Pattern
- Story generation factory based on selected AI provider
- Audio generation factory based on language and text length

### 4. Template Method Pattern
- Common story processing flow with provider-specific implementations
- Standardized error handling and logging

### 5. Observer Pattern
- Waiting page observes story generation status
- Polling mechanism for status updates

## File Organization

```
./add_test_data.py
./admin.py
./app.py
./assets/style.css
./auth.py
./check_db_structure.py
./child_storyteller_mcp.json
./config_loader.py
./db_check.py
./db_query.py
./db_utils.py
./init_db.py
./process_stories.py
./report.html
./requirements-check.py
./routes/api_routes.py
./routes/__init__.py
./routes/main_routes.py
./routes/story_routes.py
./send_email.py
./services/email_service.py
./services/__init__.py
./services/story_service.py
./static/css
./static/css/admin.css
./static/css/auth.css
./static/css/base.css
./static/css/forms.css
./static/css/rating.css
./static/css/story.css
./static/css/story_list.css
./static/css/waiting.css
./static/js
./static/js/auth.js
./static/js/base.js
./static/js/form-handlers.js
./static/js/rating.js
./static/js/story_list.js
./static/js/waiting.js
./story_metadata.json
./story_processor.py
./templates/about.html
./templates/admin/backup.html
./templates/admin/base.html
./templates/admin/configuration.html
./templates/admin/dashboard.html
./templates/admin/stories.html
./templates/admin/system.html
./templates/admin/users.html
./templates/auth/email_verified.html
./templates/auth/login.html
./templates/auth/profile.html
./templates/auth/register.html
./templates/auth/registration_pending.html
./templates/auth/resend_verification.html
./templates/auth/verification_failed.html
./templates/base.html
./templates/confirmation.html
./templates/create_story.html
./templates/email/welcome_email.html
./templates/index.html
./templates/story_list.html
./templates/story_view.html
./templates/waiting.html
./test_example_stories.py
./update_italian_translations.py
./update_portuguese_translations.py
./update_spanish_translations.py
./utils/file_utils.py
./utils/__init__.py
./utils/template_utils.py


```

## Security Patterns

1. **Authentication**: Username/password for admin access
2. **Authorization**: Admin-required decorator for protected routes
3. **Input Validation**: Form validation for story creation
4. **Path Traversal Prevention**: Security checks on file paths
5. **Error Handling**: Structured error handling and logging
6. **API Key Management**: Environment variables for API keys

## Scalability Considerations

1. **Queue-Based Processing**: Allows for horizontal scaling of processors
2. **Stateless Web Application**: Can be scaled across multiple instances
3. **File-Based Storage**: Simple but may need to be replaced for high volume
4. **Background Processing**: Offloads intensive tasks from web application
