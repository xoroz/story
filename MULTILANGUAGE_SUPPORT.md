# Multilanguage Support for StoryMagic

This document describes the multilanguage support implementation for the StoryMagic application.

## Supported Languages

The application currently supports the following languages:

- English (en) - Default
- Spanish (es)
- Portuguese (pt)
- Italian (it)

## Implementation Details

### Technology

The multilanguage support is implemented using Flask-Babel, which provides internationalization and localization support for Flask applications.

### Files and Structure

1. **babel.cfg**: Configuration file for Flask-Babel that specifies which files to scan for translatable strings.

2. **translations/**: Directory containing translation files for each supported language.
   - `en/LC_MESSAGES/messages.po` - English translations
   - `es/LC_MESSAGES/messages.po` - Spanish translations
   - `pt/LC_MESSAGES/messages.po` - Portuguese translations
   - `it/LC_MESSAGES/messages.po` - Italian translations
   - Compiled `.mo` files are generated from these `.po` files

3. **Scripts**:
   - `extract_translations.sh`: Extracts translatable strings from the application and creates/updates the `.pot` file and `.po` files.
   - `compile_translations.sh`: Compiles the `.po` files into `.mo` files that can be used by the application.
   - `update_spanish_translations.py`, `update_portuguese_translations.py`, `update_italian_translations.py`: Scripts to update the translations for each language.
   - `update_all_translations.sh`: Script to update and compile all translations at once.

### Code Changes

1. **app.py**: 
   - Configured Flask-Babel with supported languages
   - Implemented a locale selector function that determines the language based on:
     - User's session language preference
     - User's database language preference (if logged in)
     - Browser's language settings

2. **templates/base.html**:
   - Added language selector in the navigation bar
   - Added language attribute to the HTML tag based on the current locale

3. **static/js/base.js**:
   - Added `changeLanguage()` function to handle language changes
   - Added synchronization between desktop and mobile language selectors

4. **routes/main_routes.py**:
   - Added `/set-language` route to handle language changes
   - Updates user's preferred language in the database if logged in
   - Stores language preference in the session for non-logged in users

5. **auth.py**:
   - Added `preferred_language` field to the user profile
   - Updated profile page to allow users to set their preferred language

6. **templates/auth/profile.html**:
   - Added language preference selector in the user profile settings

## Translation Process

1. Mark strings for translation in templates and Python code using the `_()` function or Jinja2's `{{ _('text') }}` syntax.

2. Run `./extract_translations.sh` to extract translatable strings and create/update translation files.

3. Edit the `.po` files in the `translations/` directory to add translations for each language, or use the update scripts.

4. Run `./compile_translations.sh` to compile the translations into `.mo` files.

5. Restart the application to apply the changes.

## Adding a New Language

To add support for a new language:

1. Add the language code to the `BABEL_SUPPORTED_LOCALES` list in `app.py`.

2. Run `pybabel init -i translations/messages.pot -d translations -l <language_code>` to create the initial translation file.

3. Edit the generated `.po` file to add translations.

4. Create an update script for the new language similar to the existing ones.

5. Update the language selectors in the templates to include the new language.

6. Compile the translations and restart the application.

## User Experience

- Users can change the language using the language selector in the navigation bar.
- The selected language is stored in the session for non-logged in users.
- Logged-in users can set their preferred language in their profile settings, which will be used across sessions.
- The application will attempt to detect the user's preferred language from their browser settings if no preference is set.
