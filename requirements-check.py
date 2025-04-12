#!/usr/bin/env python3
"""
Requirements Checker - Finds unused packages in requirements.txt by analyzing imports
"""

import os
import re
import sys
from collections import defaultdict

def find_python_files(directory="."):
    """Find all Python files in the given directory, excluding venv and hidden directories"""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip hidden directories and virtual environments
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'venv' and d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    return python_files

def extract_imports(python_files):
    """Extract all imports from the given Python files"""
    # Regular expressions to match different import patterns
    import_patterns = [
        r'^\s*import\s+([\w\.]+)',                # import x
        r'^\s*from\s+([\w\.]+)\s+import',         # from x import y
        r'^\s*import\s+([\w\.]+)\s+as',           # import x as y
        r'^\s*from\s+([\w\.]+)\s+import.*\\\s*$'  # multi-line imports
    ]
    
    all_imports = set()
    multi_line_import = False
    current_import = None
    
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                for line in f:
                    # Handle continued multi-line imports
                    if multi_line_import:
                        if '\\' not in line:
                            multi_line_import = False
                        continue
                    
                    # Check each import pattern
                    for pattern in import_patterns:
                        matches = re.findall(pattern, line)
                        for match in matches:
                            if '\\' in line:  # Multi-line import detected
                                multi_line_import = True
                                current_import = match
                            
                            # Extract the top-level package
                            package = match.split('.')[0]
                            all_imports.add(package)
        except Exception as e:
            print(f"Warning: Could not process {py_file}: {e}", file=sys.stderr)
    
    return all_imports

def read_requirements(req_file="requirements.txt"):
    """Read and parse requirements.txt"""
    if not os.path.exists(req_file):
        print(f"Error: {req_file} not found", file=sys.stderr)
        return []
    
    requirements = []
    with open(req_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
                
            # Strip version specifiers
            package = re.split(r'[<>=~]', line)[0].strip().lower()
            if package:
                requirements.append(package)
    
    return requirements

def get_package_mapping():
    """Return mapping of package names to their import names"""
    return {
        'flask': 'flask',
        'django': 'django',
        'requests': 'requests',
        'beautifulsoup4': 'bs4',
        'python-dateutil': 'dateutil',
        'pillow': 'pil',
        'scikit-learn': 'sklearn',
        'numpy': 'numpy',
        'pandas': 'pandas',
        'matplotlib': 'matplotlib',
        'pytest': 'pytest',
        'sqlalchemy': 'sqlalchemy',
        'pyyaml': 'yaml',
        'jinja2': 'jinja2',
        'flask-login': 'flask_login',
        'flask-wtf': 'flask_wtf',
        'flask-sqlalchemy': 'flask_sqlalchemy',
        'werkzeug': 'werkzeug',
        'itsdangerous': 'itsdangerous',
        'click': 'click',
        # Add more mappings as needed
    }

def main():
    """Main function to check for unused requirements"""
    # Find all Python files
    print("Finding Python files...")
    python_files = find_python_files()
    print(f"Found {len(python_files)} Python files")
    
    # Extract imports
    print("Extracting imports...")
    imports = extract_imports(python_files)
    print(f"Found {len(imports)} unique imports")
    
    # Read requirements
    print("Reading requirements.txt...")
    requirements = read_requirements()
    req_count = len(requirements)
    print(f"Found {req_count} packages in requirements.txt")
    
    # Get package mapping
    package_mapping = get_package_mapping()
    
    # Check for unused packages
    unused = []
    used = []
    
    lowercase_imports = {imp.lower() for imp in imports}
    
    for package in requirements:
        package_lower = package.lower()
        
        # Check if import name is directly found
        if package_lower in lowercase_imports:
            used.append(package)
            continue
            
        # Check if any mapped import name is found
        mapped_name = package_mapping.get(package_lower)
        if mapped_name and mapped_name.lower() in lowercase_imports:
            used.append(package)
            continue
            
        # Handle special cases for Flask extensions
        if package_lower.startswith('flask-') or package_lower.startswith('flask_'):
            base_name = package_lower.replace('flask-', 'flask_')
            if base_name in lowercase_imports or f"flask.ext.{base_name.replace('flask_', '')}" in lowercase_imports:
                used.append(package)
                continue
                
        # Package not found in imports
        unused.append(package)
    
    # Print results
    print("\n=== RESULTS ===")
    print(f"Total packages in requirements.txt: {req_count}")
    print(f"Used packages: {len(used)}")
    print(f"Unused packages: {len(unused)}")
    
    if unused:
        print("\nUnused packages:")
        for package in unused:
            print(f"  - {package}")
    else:
        print("\nGreat! All packages in requirements.txt appear to be used.")
    
    # Debug: print imports for verification
    if '--debug' in sys.argv:
        print("\nAll imports found:")
        for imp in sorted(imports):
            print(f"  - {imp}")

if __name__ == "__main__":
    main()