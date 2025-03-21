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
});

/**
 * Initialize character counters for textareas with maxlength
 */
function initCharacterCounters() {
    const textareas = document.querySelectorAll('textarea[maxlength]');
    
    textareas.forEach(textarea => {
        const maxLength = textarea.getAttribute('maxlength');
        const counterId = textarea.id + '_counter';
        
        // Create counter element if it doesn't exist
        let counter = document.getElementById(counterId);
        if (!counter) {
            counter = document.createElement('div');
            counter.id = counterId;
            counter.className = 'char-counter';
            textarea.parentNode.insertBefore(counter, textarea.nextSibling);
        }
        
        // Update counter on input
        function updateCounter() {
            const currentLength = textarea.value.length;
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
        textarea.addEventListener('input', updateCounter);
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
