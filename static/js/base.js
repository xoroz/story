/**
 * Base JavaScript functionality for StoryMagic
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize flash message dismissal
    initFlashMessages();
    
    // Initialize mobile navigation
    initMobileNavigation();
    
    // Sync language selectors
    syncLanguageSelectors();
});

/**
 * Change the site language
 * @param {string} lang - The language code (en, es, pt, it)
 */
function changeLanguage(lang) {
    // Create URL for language change with current page as next parameter
    const currentUrl = encodeURIComponent(window.location.href);
    const langUrl = `/set-language?lang=${lang}&next=${currentUrl}`;
    
    // Redirect to the language change route
    window.location.href = langUrl;
}

/**
 * Sync desktop and mobile language selectors
 */
function syncLanguageSelectors() {
    const desktopSelector = document.getElementById('language-select');
    const mobileSelector = document.getElementById('mobile-language-select');
    
    if (desktopSelector && mobileSelector) {
        // Sync mobile to desktop
        desktopSelector.addEventListener('change', function() {
            mobileSelector.value = desktopSelector.value;
        });
        
        // Sync desktop to mobile
        mobileSelector.addEventListener('change', function() {
            desktopSelector.value = mobileSelector.value;
        });
    }
}

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

/**
 * Initialize mobile navigation functionality
 */
function initMobileNavigation() {
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const mobileMenuClose = document.querySelector('.mobile-menu-close');
    const mobileNav = document.querySelector('.mobile-nav');
    const body = document.body;
    
    // Create overlay element
    const overlay = document.createElement('div');
    overlay.className = 'nav-overlay';
    body.appendChild(overlay);
    
    // Toggle mobile menu
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', function() {
            toggleMobileMenu(true);
        });
    }
    
    // Close mobile menu
    if (mobileMenuClose) {
        mobileMenuClose.addEventListener('click', function() {
            toggleMobileMenu(false);
        });
    }
    
    // Close menu when clicking on overlay
    overlay.addEventListener('click', function() {
        toggleMobileMenu(false);
    });
    
    // Close menu when clicking on a mobile nav link
    const mobileNavLinks = document.querySelectorAll('.mobile-nav a');
    mobileNavLinks.forEach(link => {
        link.addEventListener('click', function() {
            toggleMobileMenu(false);
        });
    });
    
    // Toggle mobile menu function
    function toggleMobileMenu(open) {
        if (open) {
            mobileNav.style.display = 'block';
            setTimeout(() => {
                mobileNav.classList.add('active');
                overlay.classList.add('active');
                
                // Animate hamburger to X
                const spans = mobileMenuToggle.querySelectorAll('span');
                spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
                spans[1].style.opacity = '0';
                spans[2].style.transform = 'rotate(-45deg) translate(5px, -5px)';
                
                // Prevent body scrolling
                body.style.overflow = 'hidden';
            }, 10);
        } else {
            mobileNav.classList.remove('active');
            overlay.classList.remove('active');
            
            // Animate X back to hamburger
            const spans = mobileMenuToggle.querySelectorAll('span');
            spans[0].style.transform = 'none';
            spans[1].style.opacity = '1';
            spans[2].style.transform = 'none';
            
            // Re-enable body scrolling
            body.style.overflow = '';
            
            setTimeout(() => {
                mobileNav.style.display = 'none';
            }, 300);
        }
    }
}
