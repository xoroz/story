# Active Context

## Current Focus


## Next Focus



## Brainstorm ideas, improvements
 - we need to improve the story audio: ( story_process.py ) 
   1. more engaging with sounds and different voices, with rich voice content
 maybe we should try elevenlabs ?  
   2. maybe by creating a poetic form story ? 
   3. maybe by using crewai and create a whole ai agents to go full blown, story, audio,images, pdf etc..
 - we need multilanguage options 4 lang only for now ( app.py ) 
 - we need engaging form compilation , full out new chatbot audio converstation with the child user, to compile
 the needed json file for the backend ( vertical change no changes on existing code, but new external optionl like vertificalshift ? )
 - we need new addon github external auth option 
 - we need overhaul entire app for production deployment:
  1. change from flask web server to prod options fine tune for heavy load (config browser cache static, and webserver ram cahce static content)
  OK 2. security checks before going to prod, limit forms max input chars, defend for input buffers
  3. create robots.txt to index on google and others
  4. setup all its need for SEO web search highest standard
  - we need to auto export/publish on different plataforms like spotify channel/ youtube channel / x.com , we would need one channel per language, this could be a complex task and we must do one plataform at a time.
  - once we have 50 users, we should start adding payment method and allow payment via paypal only to start with credits then monthly subscriptions
  - we will need to convert the webapp into android app 

## Recent Changes

Mission accomplished! We've successfully implemented the enhanced audio feature using ElevenLabs and fixed all the audio playback issues:

Added enhanced audio option in the create_story form that uses 3 credits instead of 1
Integrated ElevenLabs API for high-quality audio generation using the official Python SDK
Fixed all audio playback issues by creating a robust routing system that handles all URL patterns
Ensured backward compatibility so all existing stories continue to work without modification
Added comprehensive error handling and logging to make future debugging easier
The system now provides users with two audio quality options:

Standard audio using OpenAI's TTS (1 credit)
Enhanced audio using ElevenLabs (3 credits)

 Fixed a simple bug on story list, we are unable to click and read the story.
 make so the title is a link to open the story.

Implemented an About section with version information, recent changes, project details, and a contact form with human verification. 

Improved Registration Form
 
Email Verification System

Enhanced welcome email with verification link

Security Enhancements, ecure token generation using cryptographic methods

Login Enhancement Completed ability to log in using either username or email. Here's what was changed:

Updated Login Form hanged the form label from "Username:" to "Username/Email:" in the login template

Added proper translation markers for multilanguage support

Added Multilanguage Support using flask_babel Created babel.cfg configuration file

improved the create story form, limit input chars on title and Main Characters  to 40.
lets create a random button on the very top to fill entire form with 8 random, pre-created and defined inside 

Database Support:

Added preferred_language field to the users table


### Email Notification System Integration (April 7, 2025)
- Renamed send-email.py to send_email.py to make it importable as a module
- Removed queue scanning/waiting functionality from email module
- Created a send_story_notification function that accepts direct parameters
- Updated story_processor.py to call the email notification function after story processing
- Updated the story link construction to use the URL from config.ini
- Ensured all logs go to the appropriate log files
- Fixed module import issues for better integration

### Database Integration (April 6, 2025)
- Added database structure definitions to config.ini
- Updated init_db.py to use database structure from config.ini
- Created process_stories.py script for manual database updates
- Updated story_processor.py to automatically update database after story creation
- Added private setting for users to control story visibility
- Added auth_type field for future authentication methods
- Made database functions more robust to handle missing columns
- Enhanced profile page to allow users to set privacy preferences
- Updated story listing and viewing to respect privacy settings

### Authentication System (Previous)
- Created auth.py module with user registration, login, logout functionality
- Implemented secure password hashing with bcrypt
- Added SQLite database with users and user_stories tables
- Created login, registration, and profile templates
- Added navigation links for login/register/logout
- Implemented credit system for story creation
- Added user profile page with credit display
- Integrated authentication with the existing application
- Added authentication check to story creation process
- Implemented credit deduction when creating stories
- Updated mobile navigation to include authentication links
- Added user-story association in the database
- Added styling for mobile authentication links

## Current Issues
- story list while not login is showing also private ones! if story is set private it should never be displayed to everyone, but only to the owner of the story.
- waiting page is not rotating the message , it should rotate current text "check waiting_waiting.js we need to create an entry in the config.ini under [app] with name "waiting_messages" with 8 different messages to have the user attention so we load the story in the background. it must update this part of the waiting.html <div class="status-message"> <p>Please wait while we generate your story...</p>    </div> s

## Debugging Strategy

### Database Integration
- Use db_utils.log to track database operations and identify issues
- Test process_stories.py with various JSON files to ensure robust handling
- Verify privacy settings are correctly applied in story listing and viewing
- Check for any performance issues with the hybrid storage approach

### Authentication System
- Ensure database is properly initialized before any authentication operations
- Use debug print statements to track route access and form submissions
- Verify session management for logged-in users
- Test credit system functionality

### Admin Dashboard
- Update admin dashboard to display and filter by user information
- Add ability to manage user privacy settings from admin interface
