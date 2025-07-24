// static/js/csrf.js
/**
 * CSRF Protection Helper
 */
(function() {
    'use strict';

    // Obține CSRF token
    function getCSRFToken() {
        // 1. Din meta tag
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) return metaTag.content;

        // 2. Din cookie
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrf_token') return value;
        }

        return null;
    }

    // Patch fetch API
    const originalFetch = window.fetch;
    window.fetch = function(url, options = {}) {
        // Adaugă CSRF pentru requests care modifică date
        const method = (options.method || 'GET').toUpperCase();
        if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
            const token = getCSRFToken();
            if (token) {
                options.headers = {
                    ...options.headers,
                    'X-CSRF-Token': token
                };
            }
        }

        return originalFetch(url, options);
    };

    // jQuery support (dacă există)
    if (typeof $ !== 'undefined') {
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                const method = (settings.type || 'GET').toUpperCase();
                if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
                    const token = getCSRFToken();
                    if (token) {
                        xhr.setRequestHeader('X-CSRF-Token', token);
                    }
                }
            }
        });
    }

    // Axios support (dacă există)
    if (typeof axios !== 'undefined') {
        axios.interceptors.request.use(config => {
            const method = (config.method || 'get').toUpperCase();
            if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
                const token = getCSRFToken();
                if (token) {
                    config.headers['X-CSRF-Token'] = token;
                }
            }
            return config;
        });
    }

    // Export pentru uz manual
    window.CSRFToken = {
        get: getCSRFToken,
        addToForm: function(form) {
            const token = getCSRFToken();
            if (token && form) {
                let input = form.querySelector('input[name="csrf_token"]');
                if (!input) {
                    input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = 'csrf_token';
                    form.appendChild(input);
                }
                input.value = token;
            }
        }
    };
})();