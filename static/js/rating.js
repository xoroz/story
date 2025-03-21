/**
 * Rating System JavaScript for StoryMagic
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize rating system
    initRatingSystem();
});

/**
 * Initialize the rating system functionality
 */
function initRatingSystem() {
    // Get all star elements
    const stars = document.querySelectorAll('.rating-stars .star');
    const ratingMessage = document.querySelector('.rating-message');
    const storyFilename = document.querySelector('.rating-container').dataset.filename;
    
    // Add click event to each star
    stars.forEach((star, index) => {
        star.addEventListener('click', function() {
            // Get the rating value (index + 1)
            const rating = index + 1;
            
            // Update visual display of stars
            updateStarsDisplay(stars, rating);
            
            // Submit the rating
            submitRating(storyFilename, rating);
        });
    });
}

/**
 * Update the visual display of stars based on rating
 * @param {NodeList} stars - The collection of star elements
 * @param {number} rating - The rating value (1-5)
 */
function updateStarsDisplay(stars, rating) {
    stars.forEach((star, index) => {
        if (index < rating) {
            star.classList.add('active');
        } else {
            star.classList.remove('active');
        }
    });
}

/**
 * Submit a rating to the server
 * @param {string} filename - The story filename
 * @param {number} rating - The rating value (1-5)
 */
function submitRating(filename, rating) {
    const ratingMessage = document.querySelector('.rating-message');
    
    // Create form data
    const formData = new FormData();
    formData.append('filename', filename);
    formData.append('rating', rating);
    
    // Send AJAX request
    fetch('/rate-story', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        // Show success message
        ratingMessage.textContent = data.message;
        ratingMessage.className = 'rating-message success';
        
        // Update rating info if provided
        if (data.average_rating !== undefined) {
            const ratingValue = document.querySelector('.rating-value');
            if (ratingValue) {
                ratingValue.textContent = data.average_rating.toFixed(1);
            }
        }
        
        if (data.rating_count !== undefined) {
            const ratingCount = document.querySelector('.rating-count');
            if (ratingCount) {
                ratingCount.textContent = `(${data.rating_count} ${data.rating_count === 1 ? 'rating' : 'ratings'})`;
            }
        }
        
        // Hide message after 3 seconds
        setTimeout(() => {
            ratingMessage.style.display = 'none';
        }, 3000);
    })
    .catch(error => {
        // Show error message
        ratingMessage.textContent = 'Error submitting rating. Please try again.';
        ratingMessage.className = 'rating-message error';
        console.error('Error:', error);
    });
}
