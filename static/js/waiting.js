/**
 * Waiting page functionality for StoryMagic
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize auto-refresh
    initAutoRefresh();
    
    // Initialize countdown timer
    initCountdownTimer();
    
    // Initialize rotating messages
    initRotatingMessages();
});

/**
 * Initialize auto-refresh functionality
 */
function initAutoRefresh() {
    const refreshInterval = document.getElementById('refresh-interval');
    
    if (!refreshInterval) return;
    
    // Get interval in seconds
    const interval = parseInt(refreshInterval.value) || 5;
    
    // Set up auto-refresh
    setTimeout(function() {
        const refreshUrl = document.getElementById('refresh-url');
        if (refreshUrl) {
            window.location.href = refreshUrl.value;
        }
    }, interval * 1000);
}

/**
 * Initialize countdown timer
 */
function initCountdownTimer() {
    const countdownElement = document.getElementById('countdown');
    const refreshInterval = document.getElementById('refresh-interval');
    
    if (!countdownElement || !refreshInterval) return;
    
    // Get interval in seconds
    let seconds = parseInt(refreshInterval.value) || 5;
    
    // Update countdown every second
    const timer = setInterval(function() {
        seconds--;
        
        if (seconds <= 0) {
            clearInterval(timer);
            countdownElement.textContent = 'Refreshing...';
        } else {
            countdownElement.textContent = `${seconds}`;
        }
    }, 1000);
}

/**
 * Initialize rotating messages
 */
function initRotatingMessages() {
    const statusMessageElement = document.querySelector('.status-message p');
    const waitingMessagesElement = document.getElementById('waiting-messages');
    
    if (!statusMessageElement || !waitingMessagesElement) {
        console.error('Status message element or waiting messages element not found');
        return;
    }
    
    // Parse the JSON string to get the array of messages
    let messages = [];
    try {
        messages = JSON.parse(waitingMessagesElement.value);
        console.log('Parsed waiting messages:', messages);
    } catch (e) {
        console.error('Error parsing waiting messages:', e);
        console.log('Raw value:', waitingMessagesElement.value);
        return;
    }
    
    if (!messages.length) {
        console.error('No waiting messages found');
        return;
    }
    
    // Set the initial message
    statusMessageElement.textContent = messages[0];
    let currentIndex = 0;
    
    // Update the message every 5 seconds
    setInterval(() => {
        // Fade out
        statusMessageElement.style.opacity = 0;
        
        // Wait for fade out to complete
        setTimeout(() => {
            // Update message
            currentIndex = (currentIndex + 1) % messages.length;
            statusMessageElement.textContent = messages[currentIndex];
            console.log('Updated to message:', messages[currentIndex]);
            
            // Fade in
            statusMessageElement.style.opacity = 1;
        }, 500);
    }, 5000);
}

/**
 * Update elapsed time since request was submitted
 */
function updateElapsedTime() {
    const elapsedElement = document.getElementById('elapsed-time');
    const startTimeElement = document.getElementById('start-time');
    
    if (!elapsedElement || !startTimeElement) return;
    
    // Get start time in milliseconds
    const startTime = parseInt(startTimeElement.value);
    if (isNaN(startTime)) return;
    
    // Calculate elapsed time
    const now = new Date().getTime();
    const elapsed = Math.floor((now - startTime) / 1000);
    
    // Format elapsed time
    let formattedTime = '';
    
    if (elapsed < 60) {
        formattedTime = `${elapsed} seconds`;
    } else if (elapsed < 3600) {
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        formattedTime = `${minutes} minute${minutes !== 1 ? 's' : ''} ${seconds} second${seconds !== 1 ? 's' : ''}`;
    } else {
        const hours = Math.floor(elapsed / 3600);
        const minutes = Math.floor((elapsed % 3600) / 60);
        formattedTime = `${hours} hour${hours !== 1 ? 's' : ''} ${minutes} minute${minutes !== 1 ? 's' : ''}`;
    }
    
    elapsedElement.textContent = formattedTime;
}

// Update elapsed time every second if on waiting page
if (document.getElementById('elapsed-time')) {
    setInterval(updateElapsedTime, 1000);
    updateElapsedTime(); // Initial update
}
