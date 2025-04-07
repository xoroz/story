def get_language_name(language_code):
    """
    Convert language code to language name
    
    Args:
        language_code: ISO language code (e.g., 'en', 'es')
        
    Returns:
        str: Human-readable language name
    """
    language_map = {
        'en': 'English',
        'es': 'Spanish',
        'it': 'Italian',
        'pt': 'Portuguese',
        'pt-br': 'Portuguese-Brazil',
    }
    return language_map.get(language_code, 'Portuguese-Brazil')

def format_story_title(filename):
    """
    Extract a formatted title from a story filename
    
    Args:
        filename: Story filename (e.g., 'my-adventure_20250407123456.html')
        
    Returns:
        str: Formatted title (e.g., 'My Adventure')
    """
    # Remove timestamp and extension
    title = ' '.join(filename.split('_')[:-1])
    # Replace hyphens with spaces and capitalize
    return title.replace('-', ' ').title()
