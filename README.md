# StoryMagic - AI-Powered Children's Story Generator

A Flask web application that generates personalized children's stories using multiple AI providers (OpenAI and DeepSeek).

## Project Structure
```
story2/
├── app.py              # Main Flask application
├── story_processor.py  # Background story generation service
├── templates/         # HTML templates
│   ├── create_story.html
│   ├── index.html
│   ├── story_list.html
│   └── waiting.html
├── stories/           # Generated story output
├── queue/            # Story generation requests
├── processed/        # Completed story requests
├── errors/          # Failed story requests
└── audio/           # Generated audio nar