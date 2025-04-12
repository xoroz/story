#!/bin/bash

# Update all translation files
echo "Updating Spanish translations..."
python update_spanish_translations.py

echo "Updating Portuguese translations..."
python update_portuguese_translations.py

echo "Updating Italian translations..."
python update_italian_translations.py

# Compile all translations
echo "Compiling translations..."
./compile_translations.sh

echo "All translations have been updated and compiled successfully!"
