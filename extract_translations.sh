#!/bin/bash

# Extract messages from Python files and templates
pybabel extract -F babel.cfg -o translations/messages.pot .

# Initialize translation catalogs for each language
pybabel init -i translations/messages.pot -d translations -l en
pybabel init -i translations/messages.pot -d translations -l es
pybabel init -i translations/messages.pot -d translations -l pt
pybabel init -i translations/messages.pot -d translations -l it

echo "Translation files created. Edit the .po files in the translations directory."
echo "After editing, compile the translations with: pybabel compile -d translations"
