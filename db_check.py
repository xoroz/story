#!/usr/bin/env python3
"""
Database Structure Checker

This script provides a simple way to check the structure of the SQLite database
and verify that it matches the expected structure from the config.ini file.
"""

import sqlite3
import os
import sys
from config_loader import load_config

def get_db_connection(db_path='database.db'):
    """Get a connection to the SQLite database"""
    if not os.path.exists(db_path):
        print(f"Error: Database file '{db_path}' not found.")
        sys.exit(1)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def check_table_structure(table_name, expected_fields=None):
    """
    Check if a table exists and has the expected structure
    
    Args:
        table_name: The name of the table to check
        expected_fields: Optional list of expected field names
    
    Returns:
        dict: Information about the table structure
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", 
        (table_name,)
    )
    if not cursor.fetchone():
        conn.close()
        return {
            'exists': False,
            'fields': [],
            'missing_fields': expected_fields or []
        }
    
    # Get table structure
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    # Get field names
    fields = [column[1] for column in columns]
    
    # Check for missing fields
    missing_fields = []
    if expected_fields:
        missing_fields = [field for field in expected_fields if field not in fields]
    
    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    row_count = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'exists': True,
        'fields': fields,
        'missing_fields': missing_fields,
        'row_count': row_count
    }

def check_db_against_config():
    """
    Check the database structure against the config.ini file
    
    Returns:
        dict: Information about the database structure
    """
    config = load_config()
    result = {'tables': {}}
    
    # Check users table
    if 'Database_Users' in config:
        table_name = config['Database_Users']['table_name']
        fields_str = config['Database_Users']['fields']
        
        # Extract field names from the fields string
        # This is a simple parser that extracts field names from the SQL field definitions
        expected_fields = []
        for field_def in fields_str.split(','):
            field_name = field_def.strip().split(' ')[0]
            if field_name and field_name != 'FOREIGN':
                expected_fields.append(field_name)
        
        result['tables'][table_name] = check_table_structure(table_name, expected_fields)
    
    # Check user_stories table
    if 'Database_UserStories' in config:
        table_name = config['Database_UserStories']['table_name']
        fields_str = config['Database_UserStories']['fields']
        
        # Extract field names from the fields string
        expected_fields = []
        for field_def in fields_str.split(','):
            field_name = field_def.strip().split(' ')[0]
            if field_name and field_name != 'FOREIGN':
                expected_fields.append(field_name)
        
        result['tables'][table_name] = check_table_structure(table_name, expected_fields)
    
    return result

def print_table_check_result(table_name, result):
    """Print the result of checking a table structure"""
    if result['exists']:
        print(f"✅ Table '{table_name}' exists")
        print(f"   Fields: {', '.join(result['fields'])}")
        
        if result['missing_fields']:
            print(f"❌ Missing fields: {', '.join(result['missing_fields'])}")
        else:
            print("✅ All expected fields are present")
        
        print(f"   Row count: {result['row_count']}")
    else:
        print(f"❌ Table '{table_name}' does not exist")
        if result['missing_fields']:
            print(f"   Expected fields: {', '.join(result['missing_fields'])}")

def main():
    """Main function"""
    print("Checking database structure against config.ini...")
    print("=" * 80)
    
    result = check_db_against_config()
    
    for table_name, table_result in result['tables'].items():
        print_table_check_result(table_name, table_result)
        print("-" * 80)
    
    # Overall assessment
    all_tables_exist = all(table['exists'] for table in result['tables'].values())
    all_fields_present = all(len(table['missing_fields']) == 0 for table in result['tables'].values())
    
    if all_tables_exist and all_fields_present:
        print("✅ Database structure is valid and matches the config.ini file")
    else:
        print("❌ Database structure has issues - see details above")

if __name__ == "__main__":
    main()
