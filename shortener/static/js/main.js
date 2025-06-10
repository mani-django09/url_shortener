// Fixed main.js - Prevents double form submission

document.addEventListener('DOMContentLoaded', function() {
    // Initialize core functionality
    initShortenForm();
    initFAQ();
    
    // Defer non-critical initializations
    requestIdleCallback(() => {
        initScrollAnimations();
        initSmoothScroll();
        initAccessibilityFeatures();
        lazyLoadImages();
        
        // Initialize tooltips only if Bootstrap is available
        if (typeof $ !== 'undefined' && $.fn.tooltip) {
            $('[data-toggle="tooltip"]').tooltip();
        }
    });
});

/**
 * FIXED: Enhanced URL shortening form - prevents double submission
 */
function initShortenForm() {
    const form = document.getElementById('shortenForm');
    if (!form) return;
    
    const button = form.querySelector('button[type="submit"]');
    const urlInput = form.querySelector('input[name="original_url"]');
    let isSubmitting = false; // Flag to prevent double submission
    
    // Add ARIA attributes for accessibility
    if (urlInput) {
        urlInput.setAttribute('aria-describedby', 'url-help');
        urlInput.addEventListener('input', debounce(validateUrl, 300));
    }
    
    form.addEventListener('submit', function(event) {
        // Prevent double submission
        if (isSubmitting) {
            event.preventDefault();
            return false;
        }
        
        const originalUrl = urlInput?.value?.trim();
        
        if (!originalUrl) {
            event.preventDefault();
            showError('Please enter a valid URL');
            urlInput?.focus();
            return false;
        }
        
        // Enhanced URL validation
        if (!isValidUrl(originalUrl)) {
            event.preventDefault();
            showError('Please enter a valid URL (including http:// or https://)');
            urlInput?.focus();
            return false;
        }
        
        // Set submission flag and show loading state
        isSubmitting = true;
        setLoadingState(true);
        
        // Let the form submit naturally to Django
        // Don't prevent default - let Django handle the redirect
        console.log('Form submitting to Django...');
        
        // Reset flag after a delay in case submission fails
        setTimeout(() => {
            isSubmitting = false;
            setLoadingState(false);
        }, 10000); // 10 second timeout
    });
    
    // Also prevent multiple rapid clicks on submit button
    if (button) {
        button.addEventListener('click', function(event) {
            if (isSubmitting) {
                event.preventDefault();
                return false;
            }
        });
    }
}

/**
 * Enhanced URL validation
 */
function isValidUrl(string) {
    try {
        // Allow URLs without protocol - Django will add https://
        if (!string.startsWith('http://') && !string.startsWith('https://')) {
            string = 'https://' + string;
        }
        const url = new URL(string);
        return url.protocol === 'http:' || url.protocol === 'https:';
    } catch {
        return false;
    }
}

/**
 * Show error message with better UX
 */
function showError(message) {
    const urlInput = document.querySelector('input[name="original_url"]');
    if (urlInput) {
        urlInput.classList.add('error-state');
        urlInput.setAttribute('aria-invalid', 'true');
        
        // Remove error state after user starts typing
        const removeError = () => {
            urlInput.classList.remove('error-state');
            urlInput.setAttribute('aria-invalid', 'false');
            urlInput.removeEventListener('input', removeError);
        };
        urlInput.addEventListener('input', removeError);
    }
    
    // Show user-friendly error notification
    showNotification(message, 'error');
}

/**
 * Set loading state with improved accessibility
 */
function setLoadingState(isLoading) {
    const form = document.getElementById('shortenForm');
    const button = form?.querySelector('button[type="submit"]');
    const normalState = button?.querySelector('.normal-state');
    const loadingSpinner = button?.querySelector('#loadingSpinner');
    
    if (!button) return;
    
    button.disabled = isLoading;
    button.setAttribute('aria-busy', isLoading.toString());
    
    if (isLoading) {
        normalState?.style && (normalState.style.display = 'none');
        loadingSpinner?.style && (loadingSpinner.style.display = 'inline-flex');
        button.setAttribute('aria-label', 'Processing your URL...');
    } else {
        normalState?.style && (normalState.style.display = 'inline-block');
        loadingSpinner?.style && (loadingSpinner.style.display = 'none');
        button.setAttribute('aria-label', 'Shorten URL');
    }
}

/**
 * Copy functionality with enhanced feedback
 */
function copyToClipboard() {
    const shortUrlElement = document.getElementById('shortUrl');
    if (!shortUrlElement) return;
    
    const textToCopy = shortUrlElement.textContent || shortUrlElement.innerText;
    
    if (!textToCopy) {
        showNotification('No URL to copy', 'error');
        return;
    }

    // Modern clipboard API with fallback
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(textToCopy).then(() => {
            handleCopySuccess();
        }).catch(() => {
            fallbackCopyToClipboard(textToCopy);
        });
    } else {
        fallbackCopyToClipboard(textToCopy);
    }
}

/**
 * Fallback copy method for older browsers
 */
function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        handleCopySuccess();
    } catch (err) {
        showNotification('Failed to copy link. Please try again.', 'error');
    } finally {
        document.body.removeChild(textArea);
    }
}

/**
 * Handle successful copy operation
 */
function handleCopySuccess() {
    showNotification('Link copied to clipboard!', 'success');
    
    const copyButton = document.querySelector('.btn-outline-primary');
    if (copyButton) {
        const icon = copyButton.querySelector('i');
        if (icon) {
            icon.classList.remove('fa-copy');
            icon.classList.add('fa-check');
            setTimeout(() => {
                icon.classList.remove('fa-check');
                icon.classList.add('fa-copy');
            }, 2000);
        }
    }
    
    // Track copy event
    trackEvent('copy_url', 'Engagement', 'URL Copied');
}

/**
 * Enhanced share functionality
 */
function shareLink() {
    const shortUrlElement = document.getElementById('shortUrl');
    if (!shortUrlElement) return;
    
    const shortUrl = shortUrlElement.textContent || shortUrlElement.innerText;
    if (!shortUrl) {
        showNotification('No URL to share', 'error');
        return;
    }
    
    const shareData = {
        title: 'Check out this shortened URL!',
        text: 'I shortened this URL using Bitly URL shortener!',
        url: shortUrl
    };

    // Use native sharing if available
    if (navigator.share && navigator.canShare && navigator.canShare(shareData)) {
        navigator.share(shareData)
            .then(() => {
                trackEvent('share_url', 'Engagement', 'URL Shared - Native');
            })
            .catch((error) => {
                if (error.name !== 'AbortError') {
                    showSocialShareOptions(shortUrl);
                }
            });
    } else {
        showSocialShareOptions(shortUrl);
    }
}

/**
 * Show social sharing options with better UX
 */
function showSocialShareOptions(url) {
    // Remove existing share popup
    const existingPopup = document.querySelector('.social-share-popup');
    if (existingPopup) {
        existingPopup.remove();
    }
    
    const socialShare = document.createElement('div');
    socialShare.className = 'social-share-popup';
    socialShare.setAttribute('role', 'dialog');
    socialShare.setAttribute('aria-label', 'Share options');
    
    const shareOptions = [
        { name: 'Twitter', icon: 'fab fa-twitter', url: `https://twitter.com/intent/tweet?url=${encodeURIComponent(url)}`, color: '#1DA1F2' },
        { name: 'Facebook', icon: 'fab fa-facebook', url: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`, color: '#4267B2' },
        { name: 'LinkedIn', icon: 'fab fa-linkedin', url: `https://www.linkedin.com/shareArticle?mini=true&url=${encodeURIComponent(url)}`, color: '#0077B5' },
        { name: 'Email', icon: 'fas fa-envelope', url: `mailto:?body=${encodeURIComponent(url)}`, color: '#EA4335' }
    ];
    
    const buttonsHTML = shareOptions.map(option => 
        `<a href="${option.url}" target="_blank" rel="noopener noreferrer" 
            class="btn btn-sm" style="background-color: ${option.color}; color: white;" 
            onclick="trackSocialShare('${option.name}')" aria-label="Share on ${option.name}">
            <i class="${option.icon}" aria-hidden="true"></i> ${option.name}
        </a>`
    ).join('');
    
    socialShare.innerHTML = `
        <div class="d-flex flex-wrap gap-2">
            ${buttonsHTML}
            <button onclick="this.closest('.social-share-popup').remove()" 
                    class="btn btn-sm btn-light" aria-label="Close share options">
                <i class="fas fa-times" aria-hidden="true"></i>
            </button>
        </div>
    `;
    
    document.body.appendChild(socialShare);
    
    // Auto-remove after 10 seconds
    setTimeout(() => {
        if (document.body.contains(socialShare)) {
            socialShare.remove();
        }
    }, 10000);
    
    // Close on escape key
    const handleEscape = (e) => {
        if (e.key === 'Escape') {
            socialShare.remove();
            document.removeEventListener('keydown', handleEscape);
        }
    };
    document.addEventListener('keydown', handleEscape);
}

/**
 * Track social share events
 */
function trackSocialShare(platform) {
    trackEvent('social_share', 'Engagement', platform);
}

/**
 * Enhanced FAQ functionality with better accessibility
 */
function initFAQ() {
    // Auto-open first FAQ item
    setTimeout(() => {
        toggleFaq(0);
    }, 1000);
    
    // Add keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (e.target.matches('.faq-question')) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                e.target.click();
            }
        }
    });
}

/**
 * Enhanced FAQ toggle with improved accessibility
 */
function toggleFaq(index) {
    const answer = document.getElementById(`faqAnswer${index}`);
    const icon = document.getElementById(`faqIcon${index}`);
    const question = icon?.closest('.faq-question');
    
    if (!answer || !icon || !question) return;
    
    const isExpanded = answer.style.display === 'block';
    
    // Close other FAQs
    document.querySelectorAll('.faq-answer').forEach((item, i) => {
        if (i !== index && item.style.display === 'block') {
            item.style.display = 'none';
            const otherIcon = document.getElementById(`faqIcon${i}`);
            const otherQuestion = otherIcon?.closest('.faq-question');
            if (otherIcon && otherQuestion) {
                otherIcon.classList.remove('fa-chevron-up');
                otherIcon.classList.add('fa-chevron-down');
                otherQuestion.setAttribute('aria-expanded', 'false');
            }
        }
    });
    
    // Toggle current FAQ
    if (isExpanded) {
        answer.style.display = 'none';
        icon.classList.remove('fa-chevron-up');
        icon.classList.add('fa-chevron-down');
        question.setAttribute('aria-expanded', 'false');
    } else {
        answer.style.display = 'block';
        icon.classList.remove('fa-chevron-down');
        icon.classList.add('fa-chevron-up');
        question.setAttribute('aria-expanded', 'true');
        
        // Track FAQ engagement
        const faqTitle = question.querySelector('h6')?.textContent;
        if (faqTitle) {
            trackEvent('faq_click', 'Engagement', faqTitle);
        }
    }
}

/**
 * Enhanced scroll animations with performance optimizations
 */
function initScrollAnimations() {
    if (!('IntersectionObserver' in window)) {
        // Fallback for browsers without IntersectionObserver
        document.querySelectorAll('.feature-card, .faq-item, .about-section').forEach(item => {
            item.classList.add('animate-in');
        });
        return;
    }
    
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe elements with requestIdleCallback for better performance
    const elementsToObserve = document.querySelectorAll('.feature-card, .faq-item, .about-section');
    
    if ('requestIdleCallback' in window) {
        requestIdleCallback(() => {
            elementsToObserve.forEach(item => observer.observe(item));
        });
    } else {
        elementsToObserve.forEach(item => observer.observe(item));
    }
}

/**
 * Smooth scrolling with reduced motion support
 */
function initSmoothScroll() {
    // Check if user prefers reduced motion
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                e.preventDefault();
                targetElement.scrollIntoView({
                    behavior: prefersReducedMotion ? 'auto' : 'smooth',
                    block: 'start'
                });
                
                // Focus management for accessibility
                targetElement.focus();
            }
        });
    });
}

/**
 * Enhanced accessibility features
 */
function initAccessibilityFeatures() {
    // Add skip link
    const skipLink = document.createElement('a');
    skipLink.href = '#main-content';
    skipLink.className = 'skip-link';
    //skipLink.textContent = 'Skip to main content';
    document.body.insertBefore(skipLink, document.body.firstChild);
    
    // Add main content landmark
    const mainContent = document.querySelector('main');
    if (mainContent && !mainContent.id) {
        mainContent.id = 'main-content';
        mainContent.setAttribute('tabindex', '-1');
    }
    
    // Enhance form accessibility
    const urlInput = document.querySelector('input[name="original_url"]');
    if (urlInput && !document.getElementById('url-help')) {
        const helpText = document.createElement('div');
        helpText.id = 'url-help';
        helpText.className = 'sr-only';
        helpText.textContent = 'Enter a valid URL starting with http:// or https://';
        urlInput.parentNode.appendChild(helpText);
    }
}

/**
 * Optimized lazy loading with modern techniques
 */
function lazyLoadImages() {
    if ('loading' in HTMLImageElement.prototype) {
        // Native lazy loading support
        document.querySelectorAll('img:not([loading])').forEach(img => {
            img.setAttribute('loading', 'lazy');
        });
    } else if ('IntersectionObserver' in window) {
        // Intersection Observer fallback
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.classList.add('loaded');
                        delete img.dataset.src;
                    }
                    imageObserver.unobserve(img);
                }
            });
        });
        
        document.querySelectorAll('img[data-src]').forEach(img => {
            img.classList.add('lazy-load');
            imageObserver.observe(img);
        });
    }
}

/**
 * Enhanced notification system with better UX
 */
function showNotification(message, type = 'info') {
    // Remove existing notifications
    document.querySelectorAll('.notification').forEach(notification => {
        notification.remove();
    });
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.setAttribute('role', 'alert');
    notification.setAttribute('aria-live', 'polite');
    
    const iconMap = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        info: 'fa-info-circle',
        warning: 'fa-exclamation-triangle'
    };
    
    notification.innerHTML = `
        <i class="fas ${iconMap[type] || iconMap.info}" aria-hidden="true"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(notification);

    // Auto-remove with animation
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (document.body.contains(notification)) {
                notification.remove();
            }
        }, 300);
    }, 3000);
}

/**
 * Utility functions
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Analytics tracking helper
 */
function trackEvent(action, category, label) {
    if (typeof gtag !== 'undefined') {
        gtag('event', action, {
            'event_category': category,
            'event_label': label
        });
    }
    
    // Facebook Pixel tracking if available
    if (typeof fbq !== 'undefined') {
        fbq('trackCustom', action, {
            category: category,
            label: label
        });
    }
}

/**
 * URL validation with real-time feedback
 */
function validateUrl(event) {
    const input = event.target;
    const value = input.value.trim();
    
    if (!value) {
        clearValidationState(input);
        return;
    }
    
    if (isValidUrl(value)) {
        input.classList.remove('error-state');
        input.classList.add('success-state');
        input.setAttribute('aria-invalid', 'false');
    } else {
        input.classList.remove('success-state');
        input.classList.add('error-state');
        input.setAttribute('aria-invalid', 'true');
    }
}

/**
 * Clear validation state
 */
function clearValidationState(input) {
    input.classList.remove('error-state', 'success-state');
    input.setAttribute('aria-invalid', 'false');
}

// Export functions for global access
window.bitlyShortener = {
    copyToClipboard,
    shareLink,
    toggleFaq,
    trackEvent,
    showNotification
};