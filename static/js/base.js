/**
 * Base JavaScript functionality for StoryMagic
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize flash message dismissal
    initFlashMessages();
});

/**
 * Initialize flash message dismissal functionality
 */
function initFlashMessages() {
    const flashMessages = document.querySelectorAll('.flash-message');
    
    flashMessages.forEach(message => {
        // Add close button to each message
        const closeButton = document.createElement('button');
        closeButton.innerHTML = '&times;';
        closeButton.className = 'flash-close';
        closeButton.style.float = 'right';
        closeButton.style.background = 'none';
        closeButton.style.border = 'none';
        closeButton.style.fontSize = '20px';
        closeButton.style.cursor = 'pointer';
        closeButton.style.marginLeft = '10px';
        
        // Add click event to close the message
        closeButton.addEventListener('click', function() {
            message.style.opacity = '0';
            setTimeout(() => {
                message.style.display = 'none';
            }, 300);
        });
        
        message.prepend(closeButton);
        
        // Add transition for smooth dismissal
        message.style.transition = 'opacity 0.3s ease';
    });
}
