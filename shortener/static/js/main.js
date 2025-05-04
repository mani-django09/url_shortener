// main.js - Main JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize FAQ accordions
    initFAQ();
    
    // Initialize form submission
    initShortenForm();
    
    // Initialize tooltips
    if (typeof $.fn.tooltip !== 'undefined') {
        $('[data-toggle="tooltip"]').tooltip();
    }
    
    // Initialize scroll animations
    initScrollAnimations();
    
    // Initialize smooth scrolling
    initSmoothScroll();
});

/**
 * Initialize the FAQ accordion functionality
 */
function initFAQ() {
    // Dynamically populate FAQs if needed
    const faqContainer = document.getElementById('faqAccordion');
    if (faqContainer && window.faqs) {
        const faqHtml = window.faqs.map((faq, index) => `
            <div class="faq-item" onclick="toggleFaq(${index})">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0 font-weight-bold">${faq.question}</h6>
                    <i class="fas fa-chevron-down" id="faqIcon${index}"></i>
                </div>
                <div class="faq-answer" id="faqAnswer${index}">
                    <p class="mb-0 text-muted">${faq.answer}</p>
                </div>
            </div>
        `).join('');
        
        faqContainer.innerHTML = faqHtml;
    }
}

/**
 * Toggle FAQ answer visibility
 * @param {number} index - The index of the FAQ to toggle
 */
function toggleFaq(index) {
    const answer = document.getElementById(`faqAnswer${index}`);
    const icon = document.getElementById(`faqIcon${index}`);
    
    // Close other FAQs
    document.querySelectorAll('.faq-answer').forEach(item => {
        if (item.id !== `faqAnswer${index}` && item.style.display === 'block') {
            item.style.display = 'none';
            const faqIndex = item.id.replace('faqAnswer', '');
            document.getElementById(`faqIcon${faqIndex}`).classList.remove('fa-chevron-up');
            document.getElementById(`faqIcon${faqIndex}`).classList.add('fa-chevron-down');
        }
    });
    
    // Toggle current FAQ
    if (answer.style.display === 'block') {
        answer.style.display = 'none';
        icon.classList.remove('fa-chevron-up');
        icon.classList.add('fa-chevron-down');
    } else {
        answer.style.display = 'block';
        icon.classList.remove('fa-chevron-down');
        icon.classList.add('fa-chevron-up');
    }
}

/**
 * Initialize the URL shortening form
 */
function initShortenForm() {
    const form = document.getElementById('shortenForm');
    if (!form) return;
    
    form.addEventListener('submit', function(event) {
        event.preventDefault();
        
        const button = form.querySelector('button[type="submit"]');
        const normalState = button.querySelector('.normal-state');
        const loading = button.querySelector('#loadingSpinner');
        
        // Show loading state
        button.disabled = true;
        if (normalState) normalState.style.display = 'none';
        if (loading) {
            loading.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            loading.style.display = 'inline-block';
        }
        
        // Get form data
        const formData = new FormData(form);
        
        // Send AJAX request
        fetch('/shorten-url/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Reset form state
            button.disabled = false;
            if (normalState) normalState.style.display = 'inline-block';
            if (loading) loading.style.display = 'none';
            
            // Update UI with shortened URL
            const shortUrlElement = document.getElementById('shortUrl');
            if (shortUrlElement) {
                shortUrlElement.textContent = data.short_url;
                shortUrlElement.setAttribute('href', data.short_url);
            }
            
            // Show result container
            const resultContainer = document.getElementById('result');
            if (resultContainer) {
                resultContainer.style.display = 'block';
            }
            
            // Show success notification
            showNotification('URL shortened successfully!', 'success');
        })
        .catch(error => {
            // Reset form state
            button.disabled = false;
            if (normalState) normalState.style.display = 'inline-block';
            if (loading) loading.style.display = 'none';
            
            // Show error notification
            showNotification('Error creating short URL. Please check the URL format and try again.', 'error');
            console.error('Error:', error);
        });
    });
}

/**
 * Copy shortened URL to clipboard
 */
function copyToClipboard() {
    const shortUrlElement = document.getElementById('shortUrl');
    if (!shortUrlElement) return;
    
    const textToCopy = shortUrlElement.textContent || shortUrlElement.innerText;
    
    if (!textToCopy) {
        showNotification('No URL to copy', 'error');
        return;
    }

    navigator.clipboard.writeText(textToCopy).then(() => {
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
    }).catch(() => {
        showNotification('Failed to copy link. Please try again.', 'error');
    });
}

/**
 * Share shortened link
 */
function shareLink() {
    const shortUrl = document.getElementById('shortUrl').textContent;
    const shareData = {
        title: 'Check out this link!',
        text: 'I shortened this URL using Bitly URL shortener!',
        url: shortUrl
    };

    if (navigator.share) {
        navigator.share(shareData)
            .then(() => showNotification('Thanks for sharing!', 'success'))
            .catch((error) => {
                if (error.name !== 'AbortError') {
                    showNotification('Error sharing link', 'error');
                }
            });
    } else {
        // Fallback for browsers that don't support native sharing
        const socialShare = document.createElement('div');
        socialShare.className = 'social-share-popup';
        socialShare.innerHTML = `
            <a href="https://twitter.com/intent/tweet?url=${encodeURIComponent(shortUrl)}" target="_blank" class="btn btn-sm" style="background-color: #1DA1F2; color: white;">
                <i class="fab fa-twitter"></i> Twitter
            </a>
            <a href="https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shortUrl)}" target="_blank" class="btn btn-sm" style="background-color: #4267B2; color: white;">
                <i class="fab fa-facebook"></i> Facebook
            </a>
            <a href="https://www.linkedin.com/shareArticle?mini=true&url=${encodeURIComponent(shortUrl)}" target="_blank" class="btn btn-sm" style="background-color: #0077B5; color: white;">
                <i class="fab fa-linkedin"></i> LinkedIn
            </a>
            <a href="mailto:?body=${encodeURIComponent(shortUrl)}" class="btn btn-sm" style="background-color: #EA4335; color: white;">
                <i class="fas fa-envelope"></i> Email
            </a>
            <button onclick="this.parentNode.remove()" class="btn btn-sm btn-light">
                <i class="fas fa-times"></i>
            </button>
        `;
        document.body.appendChild(socialShare);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (document.body.contains(socialShare)) {
                document.body.removeChild(socialShare);
            }
        }, 10000);
    }
}

/**
 * Reset form to create another shortened URL
 */
function resetForm() {
    const form = document.getElementById('shortenForm');
    if (form) {
        form.reset();
    }
    
    const resultContainer = document.getElementById('result');
    if (resultContainer) {
        resultContainer.style.display = 'none';
    }
    
    const shortUrlElement = document.getElementById('shortUrl');
    if (shortUrlElement) {
        shortUrlElement.textContent = '';
    }
}

/**
 * Show notification
 * @param {string} message - The message to display
 * @param {string} type - The type of notification (success, error)
 */
function showNotification(message, type) {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => {
        notification.remove();
    });
    
    // Create new notification
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
        ${message}
    `;
    document.body.appendChild(notification);

    // Auto-remove after 3 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

/**
 * Initialize scroll animations
 */
function initScrollAnimations() {
    // Check if IntersectionObserver is supported
    if ('IntersectionObserver' in window) {
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

        // Observe elements for animation
        document.querySelectorAll('.feature-card, .testimonial-card, .faq-item, .stats-card').forEach(item => {
            observer.observe(item);
        });
    } else {
        // Fallback for browsers that don't support IntersectionObserver
        document.querySelectorAll('.feature-card, .testimonial-card, .faq-item, .stats-card').forEach(item => {
            item.classList.add('animate-in');
        });
    }
}

/**
 * Initialize smooth scrolling for anchor links
 */
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                e.preventDefault();
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

/**
 * Lazy load images
 */
function lazyLoadImages() {
    if ('loading' in HTMLImageElement.prototype) {
        // Browser supports native lazy loading
        document.querySelectorAll('img').forEach(img => {
            img.setAttribute('loading', 'lazy');
        });
    } else {
        // Fallback for browsers that don't support native lazy loading
        // You could use a library like lozad.js here
    }
}

// Call lazy loading when DOM is loaded
document.addEventListener('DOMContentLoaded', lazyLoadImages);