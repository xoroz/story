// Client-side validation and functionality for auth pages

document.addEventListener('DOMContentLoaded', function() {
    // Form validation for registration
    const registerForm = document.querySelector('form[action="/register"]');
    if (registerForm) {
        registerForm.addEventListener('submit', function(event) {
            const username = document.getElementById('username').value;
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            if (!username || !email || !password) {
                event.preventDefault();
                alert('All fields are required.');
            }
        });
    }

    // Form validation for login
    const loginForm = document.querySelector('form[action="/login"]');
    if (loginForm) {
        loginForm.addEventListener('submit', function(event) {
            const usernameOrEmail = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            if (!usernameOrEmail || !password) {
                event.preventDefault();
                alert('Both fields are required.');
            }
        });
    }
    
    // Handle privacy toggle forms
    const privacyForms = document.querySelectorAll('.privacy-form');
    privacyForms.forEach(form => {
        const checkbox = form.querySelector('input[type="checkbox"]');
        const label = form.querySelector('.toggle-label');
        
        if (checkbox && label) {
            // Update label text when checkbox changes
            checkbox.addEventListener('change', function() {
                label.textContent = this.checked ? 'Private' : 'Public';
                
                // Show a brief message that the form is being submitted
                const row = form.closest('tr');
                if (row) {
                    row.classList.add('updating');
                    
                    // Remove the class after submission completes
                    setTimeout(() => {
                        row.classList.remove('updating');
                    }, 1000);
                }
            });
        }
    });
});
