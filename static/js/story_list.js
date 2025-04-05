document.addEventListener('DOMContentLoaded', function() {
    // Initialize variables
    const table = document.querySelector('.story-table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const filterSelects = document.querySelectorAll('.filter-select');
    const searchFilter = document.getElementById('search-filter');
    const sortableHeaders = document.querySelectorAll('.sortable');
    const selectAllCheckbox = document.getElementById('select-all');
    const playSelectedButton = document.getElementById('play-selected');
    const audioPlayer = document.getElementById('story-audio-player');
    const audioPlayerContainer = document.getElementById('audio-player-container');
    const closePlayerButton = document.getElementById('close-player');
    const currentTitleElement = document.getElementById('current-title');
    
    // Populate filter dropdowns
    populateFilters();
    
    // Set up event listeners
    setupEventListeners();
    
    // Initialize audio playlist
    let playlist = [];
    let currentTrackIndex = 0;
    
    function populateFilters() {
        // Get unique values for each filter
        const themes = new Set();
        const ages = new Set();
        const models = new Set();
        const languages = new Set();
        const usernames = new Set();
        
        rows.forEach(row => {
            themes.add(row.dataset.theme);
            ages.add(row.dataset.age);
            models.add(`${row.dataset.provider} ${row.dataset.model}`.trim());
            // Get language from dataset
            const language = row.dataset.language;
            if (language && language !== '-') {
                languages.add(language);
            }
            // Get username from dataset
            const username = row.dataset.username;
            if (username && username !== '-') {
                usernames.add(username);
            }
        });
        
        // Populate theme filter
        const themeFilter = document.getElementById('theme-filter');
        Array.from(themes)
            .filter(theme => theme)
            .sort()
            .forEach(theme => {
                const option = document.createElement('option');
                option.value = theme;
                option.textContent = theme;
                themeFilter.appendChild(option);
            });
            
        // Populate age filter
        const ageFilter = document.getElementById('age-filter');
        Array.from(ages)
            .filter(age => age)
            .sort()
            .forEach(age => {
                const option = document.createElement('option');
                option.value = age;
                option.textContent = age;
                ageFilter.appendChild(option);
            });
            
        // Populate model filter
        const modelFilter = document.getElementById('model-filter');
        Array.from(models)
            .filter(model => model)
            .sort()
            .forEach(model => {
                const option = document.createElement('option');
                option.value = model;
                option.textContent = model;
                modelFilter.appendChild(option);
            });
            
        // Add language filter if needed
        if (document.getElementById('language-filter')) {
            const languageFilter = document.getElementById('language-filter');
            Array.from(languages)
                .filter(language => language)
                .sort()
                .forEach(language => {
                    const option = document.createElement('option');
                    option.value = language;
                    option.textContent = language;
                    languageFilter.appendChild(option);
                });
        }
        
        // Add username filter if needed
        if (document.getElementById('username-filter')) {
            const usernameFilter = document.getElementById('username-filter');
            Array.from(usernames)
                .filter(username => username)
                .sort()
                .forEach(username => {
                    const option = document.createElement('option');
                    option.value = username;
                    option.textContent = username;
                    usernameFilter.appendChild(option);
                });
        }
    }
    
    function setupEventListeners() {
        // Filter change events
        filterSelects.forEach(select => {
            select.addEventListener('change', applyFilters);
        });
        
        // Search input event
        searchFilter.addEventListener('input', applyFilters);
        
        // Sort header click events
        sortableHeaders.forEach(header => {
            header.addEventListener('click', () => {
                const sortBy = header.dataset.sort;
                sortTable(sortBy, header);
            });
        });
        
        // Select all checkbox
        selectAllCheckbox.addEventListener('change', () => {
            const storyCheckboxes = document.querySelectorAll('.story-select');
            storyCheckboxes.forEach(checkbox => {
                checkbox.checked = selectAllCheckbox.checked;
            });
            updatePlaySelectedButton();
        });
        
        // Individual checkboxes
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('story-select')) {
                updatePlaySelectedButton();
            }
        });
        
        // Play selected button
        playSelectedButton.addEventListener('click', playSelectedStories);
        
        // Individual play buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('play-audio') || 
                e.target.parentElement.classList.contains('play-audio')) {
                const button = e.target.classList.contains('play-audio') ? 
                    e.target : e.target.parentElement;
                const audioPath = button.dataset.audioPath;
                const title = button.closest('tr').querySelector('.story-title-cell').textContent;
                playAudio(audioPath, title);
            }
        });
        
        // Close player button
        closePlayerButton.addEventListener('click', () => {
            audioPlayerContainer.classList.add('hidden');
            audioPlayer.pause();
            audioPlayer.src = '';
            playlist = [];
        });
        
        // Audio ended event
        audioPlayer.addEventListener('ended', playNextInPlaylist);
    }
    
    function applyFilters() {
        const themeFilter = document.getElementById('theme-filter').value;
        const ageFilter = document.getElementById('age-filter').value;
        const modelFilter = document.getElementById('model-filter').value;
        const languageFilter = document.getElementById('language-filter') ? document.getElementById('language-filter').value : '';
        const usernameFilter = document.getElementById('username-filter') ? document.getElementById('username-filter').value : '';
        const searchText = searchFilter.value.toLowerCase();
        
        rows.forEach(row => {
            const theme = row.dataset.theme;
            const age = row.dataset.age;
            const model = `${row.dataset.provider} ${row.dataset.model}`.trim();
            const language = row.dataset.language;
            const username = row.dataset.username;
            const title = row.dataset.title.toLowerCase();
            
            const themeMatch = !themeFilter || theme === themeFilter;
            const ageMatch = !ageFilter || age === ageFilter;
            const modelMatch = !modelFilter || model === modelFilter;
            const languageMatch = !languageFilter || language === languageFilter;
            const usernameMatch = !usernameFilter || username === usernameFilter;
            const searchMatch = !searchText || title.includes(searchText);
            
            if (themeMatch && ageMatch && modelMatch && languageMatch && usernameMatch && searchMatch) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }
    
    function sortTable(sortBy, header) {
        // Remove sort classes from all headers
        sortableHeaders.forEach(h => {
            h.classList.remove('sort-asc', 'sort-desc');
        });
        
        // Determine sort direction
        let sortDirection = 'asc';
        if (header.classList.contains('sort-asc')) {
            sortDirection = 'desc';
        }
        
        // Add sort class to current header
        header.classList.add(`sort-${sortDirection}`);
        
        // Sort the rows
        rows.sort((a, b) => {
            let valueA, valueB;
            
            switch(sortBy) {
                case 'title':
                    valueA = a.dataset.title;
                    valueB = b.dataset.title;
                    break;
                case 'author':
                    valueA = a.dataset.username || '';
                    valueB = b.dataset.username || '';
                    break;
                case 'date':
                    valueA = a.cells[3].textContent;
                    valueB = b.cells[3].textContent;
                    break;
                case 'theme':
                    valueA = a.dataset.theme || '';
                    valueB = b.dataset.theme || '';
                    break;
                case 'age':
                    valueA = a.dataset.age || '';
                    valueB = b.dataset.age || '';
                    break;
                case 'model':
                    valueA = `${a.dataset.provider} ${a.dataset.model}`.trim();
                    valueB = `${b.dataset.provider} ${b.dataset.model}`.trim();
                    break;
                case 'language':
                    valueA = a.cells[6].textContent.trim();
                    valueB = b.cells[6].textContent.trim();
                    break;
                case 'processing':
                    valueA = parseFloat(a.cells[7].textContent) || 0;
                    valueB = parseFloat(b.cells[7].textContent) || 0;
                    break;
                case 'audio':
                    valueA = parseFloat(a.cells[8].textContent) || 0;
                    valueB = parseFloat(b.cells[8].textContent) || 0;
                    break;
                case 'rating':
                    valueA = parseFloat(a.cells[9].querySelector('.rating-value').textContent) || 0;
                    valueB = parseFloat(b.cells[9].querySelector('.rating-value').textContent) || 0;
                    break;
                case 'views':
                    valueA = parseInt(a.cells[10].querySelector('span:last-child').textContent) || 0;
                    valueB = parseInt(b.cells[10].querySelector('span:last-child').textContent) || 0;
                    break;
                default:
                    valueA = a.cells[0].textContent;
                    valueB = b.cells[0].textContent;
            }
            
            // Compare values
            if (typeof valueA === 'number' && typeof valueB === 'number') {
                return sortDirection === 'asc' ? valueA - valueB : valueB - valueA;
            } else {
                return sortDirection === 'asc' ? 
                    valueA.localeCompare(valueB) : 
                    valueB.localeCompare(valueA);
            }
        });
        
        // Reorder the DOM
        rows.forEach(row => {
            tbody.appendChild(row);
        });
    }
    
    function updatePlaySelectedButton() {
        const selectedCheckboxes = document.querySelectorAll('.story-select:checked');
        playSelectedButton.disabled = selectedCheckboxes.length === 0;
    }
    
    function playSelectedStories() {
        const selectedCheckboxes = document.querySelectorAll('.story-select:checked');
        
        if (selectedCheckboxes.length === 0) return;
        
        // Build playlist
        playlist = Array.from(selectedCheckboxes).map(checkbox => {
            const row = checkbox.closest('tr');
            return {
                audioPath: checkbox.dataset.audioPath,
                title: row.querySelector('.story-title-cell').textContent
            };
        });
        
        // Start playing the first track
        currentTrackIndex = 0;
        playCurrentTrack();
    }
    
    function playAudio(audioPath, title) {
        // Set up single track playlist
        playlist = [{ audioPath, title }];
        currentTrackIndex = 0;
        playCurrentTrack();
    }
    
    function playCurrentTrack() {
        if (currentTrackIndex >= playlist.length) return;
        
        const track = playlist[currentTrackIndex];
        audioPlayer.src = track.audioPath;
        currentTitleElement.textContent = track.title;
        audioPlayerContainer.classList.remove('hidden');
        audioPlayer.play();
    }
    
    function playNextInPlaylist() {
        currentTrackIndex++;
        if (currentTrackIndex < playlist.length) {
            playCurrentTrack();
        } else {
            // End of playlist
            currentTrackIndex = 0;
        }
    }
});
