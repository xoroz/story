#!/usr/bin/env python3
import sqlite3
import json
import os
import sys
from tabulate import tabulate

def get_db_connection(db_path='database.db'):
    """Get a connection to the SQLite database"""
    if not os.path.exists(db_path):
        print(f"Error: Database file '{db_path}' not found.")
        sys.exit(1)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_table_names(conn):
    """Get all table names in the database"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    return [row[0] for row in cursor.fetchall()]

def get_table_info(conn, table_name):
    """Get detailed information about a table"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    
    # Get foreign keys
    cursor.execute(f"PRAGMA foreign_key_list({table_name});")
    foreign_keys = cursor.fetchall()
    
    # Get indexes
    cursor.execute(f"PRAGMA index_list({table_name});")
    indexes = cursor.fetchall()
    
    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    row_count = cursor.fetchone()[0]
    
    return {
        'columns': columns,
        'foreign_keys': foreign_keys,
        'indexes': indexes,
        'row_count': row_count
    }

def format_column_info(columns):
    """Format column information for display"""
    column_data = []
    for col in columns:
        pk = "🔑 " if col[5] else ""  # Primary key indicator
        notnull = "NOT NULL" if col[3] else "NULL"
        default = f"DEFAULT {col[4]}" if col[4] is not None else ""
        column_data.append([
            col[0],  # cid
            col[1],  # name
            f"{pk}{col[2]}",  # type with PK indicator
            notnull,  # not null
            default  # default value
        ])
    return column_data

def format_foreign_key_info(foreign_keys):
    """Format foreign key information for display"""
    if not foreign_keys:
        return []
    
    fk_data = []
    for fk in foreign_keys:
        fk_data.append([
            fk[3],  # from column
            fk[2],  # to table
            fk[4],  # to column
            fk[1],  # id
            "CASCADE" if fk[5] == 1 else fk[5],  # on delete
            "CASCADE" if fk[6] == 1 else fk[6]   # on update
        ])
    return fk_data

def format_index_info(conn, table_name, indexes):
    """Format index information for display"""
    if not indexes:
        return []
    
    cursor = conn.cursor()
    index_data = []
    
    for idx in indexes:
        # Get columns in this index
        cursor.execute(f"PRAGMA index_info({idx[1]});")
        index_columns = cursor.fetchall()
        columns = ", ".join([col[2] for col in index_columns])
        
        index_data.append([
            idx[1],  # name
            columns,  # columns
            "Unique" if idx[2] else "Regular"  # type
        ])
    
    return index_data

def check_db_structure(db_path='database.db', output_format='text'):
    """Check and output the database structure"""
    conn = get_db_connection(db_path)
    table_names = get_table_names(conn)
    
    if output_format == 'json':
        # JSON output format
        result = {"tables": {}}
        
        for table_name in table_names:
            table_info = get_table_info(conn, table_name)
            
            # Format columns
            columns = []
            for col in table_info['columns']:
                columns.append({
                    "cid": col[0],
                    "name": col[1],
                    "type": col[2],
                    "notnull": bool(col[3]),
                    "default": col[4],
                    "pk": bool(col[5])
                })
            
            # Format foreign keys
            foreign_keys = []
            for fk in table_info['foreign_keys']:
                foreign_keys.append({
                    "id": fk[0],
                    "seq": fk[1],
                    "table": fk[2],
                    "from": fk[3],
                    "to": fk[4],
                    "on_delete": fk[5],
                    "on_update": fk[6],
                    "match": fk[7]
                })
            
            # Format indexes
            indexes = []
            for idx in table_info['indexes']:
                # Get columns in this index
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA index_info({idx[1]});")
                index_columns = cursor.fetchall()
                
                index_cols = []
                for col in index_columns:
                    index_cols.append({
                        "seqno": col[0],
                        "cid": col[1],
                        "name": col[2]
                    })
                
                indexes.append({
                    "seq": idx[0],
                    "name": idx[1],
                    "unique": bool(idx[2]),
                    "origin": idx[3],
                    "partial": idx[4],
                    "columns": index_cols
                })
            
            result["tables"][table_name] = {
                "columns": columns,
                "foreign_keys": foreign_keys,
                "indexes": indexes,
                "row_count": table_info['row_count']
            }
        
        print(json.dumps(result, indent=2))
    
    else:
        # Text/tabular output format
        for table_name in table_names:
            print(f"\n{'=' * 80}")
            print(f"TABLE: {table_name}")
            print(f"{'=' * 80}")
            
            table_info = get_table_info(conn, table_name)
            
            # Display columns
            column_data = format_column_info(table_info['columns'])
            print("\nCOLUMNS:")
            print(tabulate(column_data, headers=["ID", "Name", "Type", "Null", "Default"], tablefmt="grid"))
            
            # Display foreign keys
            if table_info['foreign_keys']:
                fk_data = format_foreign_key_info(table_info['foreign_keys'])
                print("\nFOREIGN KEYS:")
                print(tabulate(fk_data, headers=["From", "To Table", "To Column", "ID", "On Delete", "On Update"], tablefmt="grid"))
            
            # Display indexes
            if table_info['indexes']:
                index_data = format_index_info(conn, table_name, table_info['indexes'])
                print("\nINDEXES:")
                print(tabulate(index_data, headers=["Name", "Columns", "Type"], tablefmt="grid"))
            
            # Display row count
            print(f"\nROW COUNT: {table_info['row_count']}")
    
    conn.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Check and output SQLite database structure')
    parser.add_argument('--db', default='database.db', help='Path to the SQLite database file')
    parser.add_argument('--format', choices=['text', 'json'], default='text', help='Output format')
    
    args = parser.parse_args()
    
    try:
        check_db_structure(args.db, args.format)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
