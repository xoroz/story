#!/usr/bin/env python3
"""
Script to process JSON files in the processed folder and populate the database
"""
import os
import sys
import argparse
from db_utils import process_json_directory, populate_story_db
from config_loader import load_config

def main():
    """Main function to process JSON files and populate the database"""
    parser = argparse.ArgumentParser(description='Process JSON files and populate the database')
    parser.add_argument('--directory', '-d', help='Directory containing JSON files to process (default: processed)')
    parser.add_argument('--file', '-f', help='Single JSON file to process')
    parser.add_argument('--force', action='store_true', help='Force processing even if user_id is missing')
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    # Process a single file if specified
    if args.file:
        file_path = args.file
        if not os.path.exists(file_path):
            # Try prepending the processed folder
            processed_folder = config['Paths']['processed_folder']
            file_path = os.path.join(processed_folder, args.file)
            if not os.path.exists(file_path):
                print(f"Error: File {args.file} does not exist")
                sys.exit(1)
        
        print(f"Processing single file: {file_path}")
        success = populate_story_db(file_path, force=args.force)
        if success:
            print("File processed successfully")
        else:
            print("Failed to process file. Check the log for details.")
        sys.exit(0 if success else 1)
    
    # Process all files in a directory
    processed_folder = args.directory if args.directory else config['Paths']['processed_folder']
    
    print(f"Processing JSON files in {processed_folder}...")
    
    # Check if directory exists
    if not os.path.exists(processed_folder):
        print(f"Error: Directory {processed_folder} does not exist")
        sys.exit(1)
    
    # Process all JSON files in the directory
    success_count, failure_count = process_json_directory(processed_folder, force=args.force)
    
    print(f"Processed {success_count + failure_count} files:")
    print(f"  - {success_count} successful")
    print(f"  - {failure_count} failed")
    
    if failure_count > 0:
        print("Check the log file for details on failed files")
    
    print("Done!")

if __name__ == '__main__':
    main()
