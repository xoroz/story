                                                                                                                                                                                                                    #!/usr/bin/env python3
"""
Database Query Tool

This script provides a simple way to query the SQLite database and display the results.
"""

import sqlite3
import os
import sys
import json
import argparse
from tabulate import tabulate

def get_db_connection(db_path='database.db'):
    """Get a connection to the SQLite database"""
    if not os.path.exists(db_path):
        print(f"Error: Database file '{db_path}' not found.")
        sys.exit(1)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def list_tables():
    """List all tables in the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    
    return tables

def get_table_data(table_name, limit=10):
    """Get data from a table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", 
        (table_name,)
    )
    if not cursor.fetchone():
        conn.close()
        print(f"Error: Table '{table_name}' does not exist.")
        return None
    
    # Get table structure
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Get data
    cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
    rows = cursor.fetchall()
    
    # Convert to list of dictionaries
    data = []
    for row in rows:
        row_dict = {}
        for i, column in enumerate(columns):
            row_dict[column] = row[i]
        data.append(row_dict)
    
    conn.close()
    
    return {
        'columns': columns,
        'data': data
    }

def print_table_data(table_name, data, format='table'):
    """Print table data in the specified format"""
    if not data:
        return
    
    if format == 'json':
        print(json.dumps(data['data'], indent=2))
    else:
        # Convert data to list of lists for tabulate
        rows = []
        for row in data['data']:
            rows.append([row[column] for column in data['columns']])
        
        print(f"\nTable: {table_name}")
        print(tabulate(rows, headers=data['columns'], tablefmt="grid"))
        print(f"Total rows: {len(data['data'])}")

def execute_query(query, format='table'):
    """Execute a custom SQL query"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        
        if not rows:
            print("Query returned no results.")
            conn.close()
            return
        
        # Get column names
        columns = [description[0] for description in cursor.description]
        
        # Convert to list of dictionaries
        data = []
        for row in rows:
            row_dict = {}
            for i, column in enumerate(columns):
                row_dict[column] = row[i]
            data.append(row_dict)
        
        if format == 'json':
            print(json.dumps(data, indent=2))
        else:
            # Convert data to list of lists for tabulate
            table_rows = []
            for row in data:
                table_rows.append([row[column] for column in columns])
            
            print("\nQuery Results:")
            print(tabulate(table_rows, headers=columns, tablefmt="grid"))
            print(f"Total rows: {len(data)}")
        
    except sqlite3.Error as e:
        print(f"Error executing query: {str(e)}")
    
    conn.close()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Query the SQLite database')
    parser.add_argument('--table', help='Table to query')
    parser.add_argument('--query', help='Custom SQL query to execute')
    parser.add_argument('--format', choices=['table', 'json'], default='table', help='Output format')
    parser.add_argument('--limit', type=int, default=10, help='Limit number of rows returned')
    
    args = parser.parse_args()
    
    if args.query:
        # Execute custom query
        execute_query(args.query, args.format)
    elif args.table:
        # Query specific table
        data = get_table_data(args.table, args.limit)
        print_table_data(args.table, data, args.format)
    else:
        # List tables
        tables = list_tables()
        print("Available tables:")
        for table in tables:
            print(f"- {table}")
        print("\nUse --table <table_name> to view table data")
        print("Use --query \"SQL QUERY\" to execute a custom query")

if __name__ == "__main__":
    main()
