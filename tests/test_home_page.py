import pytest
from playwright.sync_api import Page, expect

# Import has_text to use in filters
from playwright.sync_api._generated import Locator
has_text = Locator.has_text

# Base URL of the application
BASE_URL = "http://localhost:8000"

def test_home_page_loads(page: Page):
    """Test that the home page loads successfully"""
    # Navigate to the home page
    page.goto(BASE_URL)
    
    # Verify the page title
    expect(page.title()).to_contain("StoryMagic")
    
    # Verify that the page contains some content
    main_content = page.locator("main")
    expect(main_content).to_be_visible()
    
    # Verify navigation links are present
    nav = page.locator("nav")
    expect(nav).to_be_visible()
    
    # Check for Create Story link - use contains_text instead of text= selector
    create_link = page.locator("a").filter(has_text="Create")
    expect(create_link).to_be_visible()
    
    # Check for View Stories link - use contains_text instead of text= selector
    view_stories_link = page.locator("a").filter(has_text="Stories")
    expect(view_stories_link).to_be_visible()

def test_navigation_links(page: Page):
    """Test that navigation links work correctly"""
    # Navigate to the home page
    page.goto(BASE_URL)
    
    # Click the Create Story link - use a more general selector
    create_link = page.locator("a").filter(has_text="Create")
    create_link.click()
    
    # Verify we're on the create story page
    page.wait_for_load_state("networkidle")
    assert "/create" in page.url, f"Expected URL to contain '/create', got: {page.url}"
    
    # Go back to the home page
    page.goto(BASE_URL)
    
    # Click the View Stories link - use a more general selector
    view_stories_link = page.locator("a").filter(has_text="Stories")
    view_stories_link.click()
    
    # Verify we're on the stories page
    page.wait_for_load_state("networkidle")
    expect(page.url).to_contain("/stories")