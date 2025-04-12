import json
import configparser

# Load config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# Get example_stories from config
example_stories_str = config['App'].get('example_stories', '[]')
print("Raw example_stories string from config.ini:")
print(example_stories_str)
print("\n")

# Try to parse as JSON
try:
    example_stories = json.loads(example_stories_str)
    print("Successfully parsed as JSON:")
    print(json.dumps(example_stories, indent=2))
    print(f"Number of stories: {len(example_stories)}")
except json.JSONDecodeError as e:
    print(f"Error parsing JSON: {e}")
    print("Error at position:", e.pos)
    print("Line:", e.lineno)
    print("Column:", e.colno)
    
    # Try to fix the JSON string
    print("\nAttempting to fix the JSON string...")
    # Sometimes ConfigParser adds escape characters or quotes
    fixed_str = example_stories_str.replace('\\"', '"').replace('\\\\', '\\')
    try:
        example_stories = json.loads(fixed_str)
        print("Successfully parsed fixed JSON:")
        print(json.dumps(example_stories, indent=2))
        print(f"Number of stories: {len(example_stories)}")
    except json.JSONDecodeError as e2:
        print(f"Still error parsing JSON after fix: {e2}")
