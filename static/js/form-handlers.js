/**
 * Form handling functionality for StoryMagic
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize character counter for textareas
    initCharacterCounters();
    
    // Initialize backend selector
    initBackendSelector();
    
    // Initialize form validation
    initFormValidation();
    
    // Initialize random story button
    initRandomStoryButton();
});

/**
 * Initialize character counters for inputs and textareas with maxlength
 */
function initCharacterCounters() {
    // Handle both input fields and textareas with maxlength
    const elements = document.querySelectorAll('input[maxlength], textarea[maxlength]');
    
    elements.forEach(element => {
        const maxLength = element.getAttribute('maxlength');
        const counterId = element.id + '_counter';
        
        // Create counter element if it doesn't exist
        let counter = document.getElementById(counterId);
        if (!counter) {
            counter = document.createElement('div');
            counter.id = counterId;
            counter.className = 'char-counter';
            element.parentNode.insertBefore(counter, element.nextSibling);
        }
        
        // Update counter on input
        function updateCounter() {
            const currentLength = element.value.length;
            counter.textContent = `${currentLength}/${maxLength} characters`;
            
            // Add warning class when approaching limit
            if (currentLength > maxLength * 0.8) {
                counter.classList.add('warning');
            } else {
                counter.classList.remove('warning');
            }
        }
        
        // Initial update
        updateCounter();
        
        // Add event listener
        element.addEventListener('input', updateCounter);
    });
}

/**
 * Initialize backend selector functionality
 */
function initBackendSelector() {
    const backendCards = document.querySelectorAll('.backend-card');
    const backendInput = document.getElementById('backend');
    
    if (!backendCards.length || !backendInput) return;
    
    // Add click event to each backend card
    backendCards.forEach(card => {
        card.addEventListener('click', function() {
            const backend = this.dataset.backend;
            
            // Update hidden input
            backendInput.value = backend;
            
            // Update UI
            backendCards.forEach(c => {
                if (c.dataset.backend === backend) {
                    c.classList.add('active');
                } else {
                    c.classList.remove('active');
                }
            });
            
            // Hide all model selections
            document.querySelectorAll('.model-selection').forEach(div => {
                div.style.display = 'none';
                
                // Change name attributes so only the selected provider's model is submitted
                const select = div.querySelector('select');
                if (select) {
                    select.name = div.id.replace('-models', '_model');
                }
            });
            
            // Show selected provider's models
            const modelDiv = document.getElementById(backend + '-models');
            if (modelDiv) {
                modelDiv.style.display = 'block';
                const select = modelDiv.querySelector('select');
                if (select) {
                    select.name = 'ai_model';
                }
            }
        });
    });
}

/**
 * Initialize random story button functionality
 */
function initRandomStoryButton() {
    const randomButton = document.getElementById('random-story-btn');
    if (!randomButton) return;
    
    randomButton.addEventListener('click', function() {
        // Use the global exampleStories variable
        if (!window.exampleStories || !window.exampleStories.length) {
            console.error('No example stories available');
            return;
        }
        
        try {
            // Select a random story
            const randomStory = window.exampleStories[Math.floor(Math.random() * window.exampleStories.length)];
            
            // Fill form fields
            document.getElementById('title').value = randomStory.title || '';
            
            // Set age range
            const ageRangeSelect = document.getElementById('age_range');
            if (ageRangeSelect) {
                const ageOption = Array.from(ageRangeSelect.options).find(option => option.value === randomStory.age_range);
                if (ageOption) ageRangeSelect.value = randomStory.age_range;
            }
            
            // Set theme
            const themeSelect = document.getElementById('theme');
            if (themeSelect && randomStory.theme) {
                themeSelect.value = randomStory.theme;
            }
            
            // Set story about
            const storyAboutTextarea = document.getElementById('story_about');
            if (storyAboutTextarea) {
                storyAboutTextarea.value = randomStory.story_about || '';
            }
            
            // Set lesson
            const lessonSelect = document.getElementById('lesson');
            if (lessonSelect && randomStory.lesson) {
                const lessonOption = Array.from(lessonSelect.options).find(option => option.value === randomStory.lesson);
                if (lessonOption) lessonSelect.value = randomStory.lesson;
            }
            
            // Set characters
            const charactersInput = document.getElementById('characters');
            if (charactersInput) {
                charactersInput.value = randomStory.characters || '';
            }
            
            // Set length
            const lengthSelect = document.getElementById('length');
            if (lengthSelect && randomStory.length) {
                const lengthOption = Array.from(lengthSelect.options).find(option => option.value === randomStory.length);
                if (lengthOption) lengthSelect.value = randomStory.length;
            }
            
            // Set language
            const languageSelect = document.getElementById('language');
            if (languageSelect && randomStory.language) {
                const languageOption = Array.from(languageSelect.options).find(option => option.value === randomStory.language);
                if (languageOption) languageSelect.value = randomStory.language;
            }
            
            // Trigger input events to update character counters
            document.querySelectorAll('input[maxlength], textarea[maxlength]').forEach(el => {
                el.dispatchEvent(new Event('input'));
            });
        } catch (error) {
            console.error('Error parsing example stories:', error);
        }
    });
}

/**
 * Initialize form validation
 */
function initFormValidation() {
    const storyForm = document.querySelector('form[action*="create_story"]');
    
    if (!storyForm) return;
    
    storyForm.addEventListener('submit', function(event) {
        let isValid = true;
        
        // Validate required fields
        const requiredFields = storyForm.querySelectorAll('[required]');
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                isValid = false;
                field.classList.add('is-invalid');
                
                // Create error message if it doesn't exist
                let errorMsg = field.nextElementSibling;
                if (!errorMsg || !errorMsg.classList.contains('invalid-feedback')) {
                    errorMsg = document.createElement('div');
                    errorMsg.className = 'invalid-feedback';
                    errorMsg.textContent = 'This field is required';
                    field.parentNode.insertBefore(errorMsg, field.nextSibling);
                }
            } else {
                field.classList.remove('is-invalid');
                
                // Remove error message if it exists
                const errorMsg = field.nextElementSibling;
                if (errorMsg && errorMsg.classList.contains('invalid-feedback')) {
                    errorMsg.remove();
                }
            }
        });
        
        if (!isValid) {
            event.preventDefault();
            
            // Scroll to first invalid field
            const firstInvalid = storyForm.querySelector('.is-invalid');
            if (firstInvalid) {
                firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                firstInvalid.focus();
            }
        }
    });
}
