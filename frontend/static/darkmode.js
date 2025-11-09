// Global Dark Mode Handler
(function() {
    'use strict';
    
    // Apply dark mode immediately on page load (before DOM fully loads)
    function applyDarkMode() {
        try {
            const savedPrefs = localStorage.getItem('userPreferences');
            if (savedPrefs) {
                const prefs = JSON.parse(savedPrefs);
                console.log('🔍 Dark Mode Check:', prefs.dark_mode === true ? 'ENABLED' : 'DISABLED', '| Stored value:', prefs.dark_mode);
                if (prefs.dark_mode === true) {
                    document.documentElement.classList.add('dark-mode');
                    document.body.classList.add('dark-mode');
                    console.log('🌙 Dark mode applied');
                } else {
                    console.log('☀️ Light mode active (default)');
                }
            } else {
                console.log('☀️ No preferences found - Light mode active (default)');
            }
        } catch (error) {
            console.error('Error loading dark mode preference:', error);
        }
    }
    
    // Apply immediately
    applyDarkMode();
    
    // Also apply when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applyDarkMode);
    } else {
        applyDarkMode();
    }
    
    // Listen for storage changes (when dark mode is changed in another tab/page)
    window.addEventListener('storage', function(e) {
        if (e.key === 'userPreferences') {
            applyDarkMode();
        }
    });
})();
