#!/bin/bash

# StoryMagic API Dynamic Test Script
# This script sends random story generation requests using values from MCP JSON

# Configuration
SERVER_URL="http://localhost:8000"
QUEUE_ENDPOINT="/create"
OUTPUT_DIR="./test_output"
MCP_FILE="child_storyteller_mcp.json"

# Create output directory if it doesn't exist
mkdir -p $OUTPUT_DIR

# Function to extract values from JSON using jq
# Make sure jq is installed: apt-get install jq or brew install jq
check_jq() {
    if ! command -v jq &> /dev/null; then
        echo "Error: jq is not installed but required for parsing JSON."
        echo "Install with: sudo apt-get install jq (Linux) or brew install jq (Mac)"
        exit 1
    fi
}

# Parse MCP JSON file
parse_mcp() {
    if [ ! -f "$MCP_FILE" ]; then
        echo "Error: MCP file not found at $MCP_FILE"
        exit 1
    fi
    
    # Extract themes (keys only)
    THEMES=($(jq -r '.themes | keys[]' "$MCP_FILE"))
    
    # Extract lessons
    LESSONS=($(jq -r '.lessons[]' "$MCP_FILE"))
    
    # Extract AI providers and their models
    AI_PROVIDERS=($(jq -r '.ai_providers | keys[]' "$MCP_FILE"))
    
    # For storing provider:model pairs
    declare -g -A AI_MODELS
    
    # Loop through providers
    for provider in "${AI_PROVIDERS[@]}"; do
        # Get models for this provider
        models=($(jq -r ".ai_providers.\"$provider\".models | keys[]" "$MCP_FILE"))
        
        # Store each provider:model pair
        for model in "${models[@]}"; do
            key="$provider:$model"
            AI_MODELS["$key"]="$model"
        done
    done
    
    echo "Parsed MCP data:"
    echo "- Found ${#THEMES[@]} themes"
    echo "- Found ${#LESSONS[@]} lessons"
    echo "- Found ${#AI_PROVIDERS[@]} AI providers with ${#AI_MODELS[@]} total models"
}

# Other parameters arrays (not from MCP)
AGE_RANGES=("3-6" "7-9" "10-12")
LENGTHS=("short" "medium" "long")
CHARACTERS=(
  "Diego a 5 years old, Sofia 5 years, Wise school Teacher Maria,Magical Unicorn"
  "Diego a 5 years old, robot friend"
  "Diego a 5 years old twin brothers with magical powers"
  "Diego a 5 years old  shy dinosaur who loves to dance"
  "a group of space explorers from different planets that meets Diego"
)
LANGUAGES=("en" "es" "pt" "it")
LANGUAGES=("pt" "it")

# Function to get a random item from an array
random_item() {
    local array=("$@")
    echo "${array[RANDOM % ${#array[@]}]}"
}

# Function to generate a story
generate_story() {
    local story_num=$1
    local backend_model=$2
    
    # Parse backend and model
    IFS=':' read -r backend model <<< "$backend_model"
    
    # Generate random parameters
    local title="Test Story $story_num - $backend $model"
    local theme=$(random_item "${THEMES[@]}")
    local lesson=$(random_item "${LESSONS[@]}")
    local age_range=$(random_item "${AGE_RANGES[@]}")
    local length=$(random_item "${LENGTHS[@]}")
    local characters=$(random_item "${CHARACTERS[@]}")
    local language=$(random_item "${LANGUAGES[@]}")
    
    # Generate a random story
    echo "Generating story $story_num with $backend ($model)..."
    
    # Form data for the request
    local response=$(curl -s -X POST "$SERVER_URL$QUEUE_ENDPOINT" \
        -F "title=$title" \
        -F "theme=$theme" \
        -F "lesson=$lesson" \
        -F "age_range=$age_range" \
        -F "length=$length" \
        -F "characters=$characters" \
        -F "language=$language" \
        -F "backend=$backend" \
        -F "ai_model=$model" \
        -F "enable_audio=true")
    
    # Extract request_id from the response
    # This assumes the response redirects to waiting with a request_id parameter
    local request_id=$(echo "$response" | grep -o 'request_id=[a-f0-9-]*' | cut -d= -f2)
    
    if [ -n "$request_id" ]; then
        echo "  Success! Request ID: $request_id"
        echo "  Details: $theme story about $characters in $language"
        echo "  Check status at: $SERVER_URL/waiting/$request_id"
        
        # Save request info
        cat > "$OUTPUT_DIR/story_$story_num.txt" << EOF
Story $story_num
--------------
Request ID: $request_id
Title: $title
Theme: $theme
Lesson: $lesson
Characters: $characters
Age Range: $age_range
Length: $length
Language: $language
Backend: $backend
Model: $model
URL: $SERVER_URL/waiting/$request_id

EOF
    else
        echo "  Error generating story. Response:"
        echo "$response" | head -n 20
    fi
    
    echo "-------------------------------------------"
}

# Main script
check_jq
echo "===== StoryMagic API Dynamic Test ====="

# Parse MCP
echo "Loading story parameters from $MCP_FILE..."
parse_mcp
echo

# Number of stories to generate
if [ -n "$1" ]; then
    NUM_STORIES=$1
else
    NUM_STORIES=${#AI_MODELS[@]}
    echo "No story count specified, defaulting to one story per model ($NUM_STORIES total)"
fi

# Loop through backend/model combinations
story_num=1
for backend_model in "${!AI_MODELS[@]}"; do
    if [ $story_num -le $NUM_STORIES ]; then
        generate_story $story_num "$backend_model"
        story_num=$((story_num+1))
        # Small delay between requests
        sleep 2
    fi
done

echo
echo "Done! Generated $((story_num-1)) random stories."
echo "Request details saved in $OUTPUT_DIR/"
echo