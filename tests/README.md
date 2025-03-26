# StoryMagic Tests

This directory contains automated tests for the StoryMagic application using pytest and Playwright.

## Test Structure

The test suite is organized as follows:

- **test_home_page.py**: Tests for the home page functionality
  - Verifies the home page loads correctly
  - Checks navigation links work properly

- **test_stories_page.py**: Tests for stories listing and viewing
  - Verifies the stories page loads correctly
  - Tests story card elements
  - Tests navigation to individual story view

- **test_create_story.py**: Tests for the story creation form
  - Verifies the form loads correctly
  - Tests that form elements (dropdowns, inputs) are present

- **test_admin_login.py**: Tests for the admin dashboard authentication
  - Verifies the admin URL is accessible
  - Tests authentication with the default credentials

## Running Tests

Tests can be run using the `test-all.sh` script in the root directory:

```bash
./test-all.sh
```

Alternatively, you can run specific test files with pytest directly:

```bash
# Run a specific test file
python -m pytest tests/test_home_page.py

# Run tests with higher verbosity
python -m pytest tests/ -v

# Run tests and generate HTML report
python -m pytest tests/ --html=test-results/report.html
```

## Test Results

HTML test reports are generated in the `test-results` directory.

## Troubleshooting

If tests are failing:

1. **Server Availability**: Make sure the main application is running on port 8000 and admin on port 8001
2. **Playwright Installation**: Ensure Playwright and browsers are installed correctly
3. **Element Selectors**: If UI changes have been made, selectors in tests may need updating
4. **Authentication**: For admin tests, verify the default credentials (admin/admin123) are still valid