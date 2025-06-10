"""
Models for the URL shortener application.

This file contains the database models for the URL shortener, including:
- ShortenedURL: Main model for storing shortened URLs with SEO metadata
- ClickEvent: Tracking clicks on shortened URLs
- BlockedDomain: Managing blocked domains for security
- SuspiciousActivity: Logging suspicious activities for security monitoring
"""

import hashlib
import string
import random
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.urls import reverse


class ShortenedURL(models.Model):
    """
    Main model for storing shortened URLs with analytics and SEO metadata.
    """
    # Base URL fields
    original_url = models.URLField(max_length=2000, help_text="The original long URL")
    short_code = models.CharField(max_length=100, unique=True, db_index=True, help_text="Unique short code for the URL")
    custom_code = models.CharField(max_length=50, blank=True, null=True, db_index=True, help_text="Custom code provided by user")
    
    # Analytics fields
    clicks = models.PositiveIntegerField(default=0, help_text="Number of times this URL has been clicked")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, help_text="When this shortened URL was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="When this shortened URL was last updated")
    
    # Security fields
    url_hash = models.CharField(max_length=64, db_index=True, help_text="Hash of the original URL for duplicate detection")
    created_by_ip = models.GenericIPAddressField(default='0.0.0.0', help_text="IP address that created this URL")
    last_checked = models.DateTimeField(default=timezone.now, help_text="When this URL was last checked for security")
    is_malicious = models.BooleanField(default=False, help_text="Whether this URL has been flagged as malicious")
    is_active = models.BooleanField(default=True, help_text="Whether this URL is active and can be used")
    
    # Meta fields for SEO
    meta_title = models.CharField(max_length=60, blank=True, null=True, help_text="Custom SEO title for this URL")
    meta_description = models.CharField(max_length=160, blank=True, null=True, help_text="Custom SEO description for this URL")
    meta_keywords = models.CharField(max_length=200, blank=True, null=True, help_text="Custom SEO keywords for this URL")
    
    # Additional metadata
    expiry_date = models.DateTimeField(null=True, blank=True, help_text="When this URL will expire (null for never)")
    tags = models.CharField(max_length=255, blank=True, null=True, help_text="Comma-separated tags for categorization")
    notes = models.TextField(blank=True, null=True, help_text="Private notes about this URL")
    
    # Relations to other models
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='shortened_urls',
        help_text="User who created this URL (if authenticated)"
    )
    
    class Meta:
        verbose_name = "Shortened URL"
        verbose_name_plural = "Shortened URLs"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['short_code', 'custom_code']),
            models.Index(fields=['created_at', 'clicks']),
            models.Index(fields=['url_hash']),
            models.Index(fields=['is_active', 'expiry_date']),
        ]
    
    def __str__(self):
        """String representation of the model."""
        if self.custom_code:
            return f"{self.custom_code} → {self.original_url[:50]}{'...' if len(self.original_url) > 50 else ''}"
        return f"{self.short_code} → {self.original_url[:50]}{'...' if len(self.original_url) > 50 else ''}"
    
    def save(self, *args, **kwargs):
        """Override save method to generate short code and hash."""
        # Generate short code if not provided
        if not self.short_code:
            self.short_code = self.generate_unique_code()
        
        # Generate URL hash if not provided
        if not self.url_hash:
            self.url_hash = hashlib.sha256(self.original_url.encode()).hexdigest()
        
        super().save(*args, **kwargs)
    
    def generate_unique_code(self, length=6):
        """Generate a unique short code."""
        characters = string.ascii_letters + string.digits
        while True:
            code = ''.join(random.choices(characters, k=length))
            if not ShortenedURL.objects.filter(short_code=code).exists():
                return code
    
    def get_absolute_url(self):
        """Get the absolute URL for this shortened URL."""
        return reverse('redirect_url', kwargs={'short_code': self.short_code})
    
    def get_short_url(self):
        """Get the complete shortened URL including domain."""
        domain = getattr(settings, 'SITE_DOMAIN', 'bitly.works')
        return f"https://{domain}/{self.short_code}"
    
    def get_qr_code_url(self):
        """Get the URL for the QR code of this shortened URL."""
        return reverse('qr_code', kwargs={'short_code': self.short_code})
    
    def get_analytics_url(self):
        """Get the URL for the analytics page of this shortened URL."""
        return reverse('url_analytics', kwargs={'short_code': self.short_code})
    
    def is_expired(self):
        """Check if the URL has expired."""
        if not self.expiry_date:
            return False
        return timezone.now() > self.expiry_date
    
    def increment_clicks(self):
        """Increment the click count for this URL."""
        self.clicks += 1
        self.save(update_fields=['clicks'])
    
    # SEO Methods
    def get_meta_title(self):
        """Get SEO title or fallback to default."""
        if self.meta_title:
            return self.meta_title
        return f"{self.custom_code if self.custom_code else self.short_code} - Bitly URL Shortener"
    
    def get_meta_description(self):
        """Get SEO description or fallback to default."""
        if self.meta_description:
            return self.meta_description
        return f"Track clicks and analytics for your shortened URL {self.get_short_url()}. Free URL shortener with powerful features."
    
    def get_meta_keywords(self):
        """Get SEO keywords or fallback to default."""
        if self.meta_keywords:
            return self.meta_keywords
        return f"url shortener, short link, {self.short_code}, bitly, link analytics"
    
    def get_structured_data(self):
        """Get structured data (schema.org) for this URL."""
        return {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": self.get_meta_title(),
            "description": self.get_meta_description(),
            "url": self.get_short_url(),
            "dateCreated": self.created_at.isoformat(),
            "dateModified": self.updated_at.isoformat(),
        }


class ClickEvent(models.Model):
    """
    Model for tracking each click on a shortened URL with analytics data.
    """
    url = models.ForeignKey(
        ShortenedURL, 
        on_delete=models.CASCADE, 
        related_name='click_events',
        help_text="The shortened URL that was clicked"
    )
    clicked_at = models.DateTimeField(auto_now_add=True, db_index=True, help_text="When this click occurred")
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="IP address of the clicker")
    user_agent = models.TextField(null=True, blank=True, help_text="User agent of the browser used")
    referrer = models.URLField(max_length=2000, null=True, blank=True, help_text="Where the user came from")
    country = models.CharField(max_length=2, null=True, blank=True, help_text="ISO country code of the clicker")
    city = models.CharField(max_length=100, null=True, blank=True, help_text="City of the clicker")
    device_type = models.CharField(max_length=20, null=True, blank=True, help_text="Type of device used (desktop, mobile, tablet)")
    browser = models.CharField(max_length=50, null=True, blank=True, help_text="Browser used")
    os = models.CharField(max_length=50, null=True, blank=True, help_text="Operating system used")
    
    class Meta:
        verbose_name = "Click Event"
        verbose_name_plural = "Click Events"
        ordering = ['-clicked_at']
        indexes = [
            models.Index(fields=['clicked_at']),
            models.Index(fields=['country', 'city']),
            models.Index(fields=['device_type', 'browser', 'os']),
        ]
    
    def __str__(self):
        """String representation of the model."""
        return f"Click on {self.url.short_code} at {self.clicked_at.strftime('%Y-%m-%d %H:%M:%S')}"


class BlockedDomain(models.Model):
    """
    Model for storing blocked domains that shouldn't be shortened.
    """
    domain = models.CharField(max_length=255, unique=True, db_index=True, help_text="Domain to block")
    reason = models.TextField(help_text="Reason for blocking this domain")
    is_regex = models.BooleanField(default=False, help_text="Whether the domain pattern is a regex")
    date_added = models.DateTimeField(auto_now_add=True, help_text="When this domain was blocked")
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="User who added this blocked domain"
    )
    
    class Meta:
        verbose_name = "Blocked Domain"
        verbose_name_plural = "Blocked Domains"
        ordering = ['domain']
        indexes = [
            models.Index(fields=['domain']),
            models.Index(fields=['is_regex']),
        ]
    
    def __str__(self):
        """String representation of the model."""
        return f"{self.domain} (blocked: {self.date_added.strftime('%Y-%m-%d')})"


class SuspiciousActivity(models.Model):
    """
    Model for logging suspicious activities for security monitoring.
    """
    ACTIVITY_TYPES = (
        ('MALICIOUS_URL', 'Malicious URL Attempt'),
        ('SPAM', 'Spam Activity'),
        ('RATE_LIMIT', 'Rate Limit Exceeded'),
        ('BLOCKED_DOMAIN', 'Blocked Domain Attempt'),
        ('SECURITY_SCAN', 'Security Scan Detected'),
        ('OTHER', 'Other Suspicious Activity'),
    )
    
    ip_address = models.GenericIPAddressField(help_text="IP address of the suspicious activity")
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES, help_text="Type of suspicious activity")
    url_attempted = models.URLField(max_length=2000, help_text="URL that was attempted to be shortened")
    user_agent = models.TextField(help_text="User agent of the requester")
    request_data = models.TextField(blank=True, null=True, help_text="Any additional request data")
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True, help_text="When this activity occurred")
    is_blocked = models.BooleanField(default=True, help_text="Whether this IP is now blocked")
    notes = models.TextField(blank=True, null=True, help_text="Additional notes about this activity")
    
    class Meta:
        verbose_name = "Suspicious Activity"
        verbose_name_plural = "Suspicious Activities"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['activity_type']),
            models.Index(fields=['is_blocked']),
        ]
    
    def __str__(self):
        """String representation of the model."""
        return f"{self.get_activity_type_display()} from {self.ip_address} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


class ActivityLog(models.Model):
    """
    General activity log for system activities.
    """
    ACTION_TYPES = (
        ('CREATE', 'URL Created'),
        ('CLICK', 'URL Clicked'),
        ('DELETE', 'URL Deleted'),
        ('UPDATE', 'URL Updated'),
        ('BLOCK', 'Domain Blocked'),
        ('UNBLOCK', 'Domain Unblocked'),
        ('SECURITY', 'Security Event'),
        ('SYSTEM', 'System Event'),
    )
    
    action = models.CharField(max_length=20, choices=ACTION_TYPES, help_text="Type of action performed")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="User who performed the action"
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="IP address of the actor")
    object_id = models.CharField(max_length=50, null=True, blank=True, help_text="ID of the affected object")
    object_type = models.CharField(max_length=50, null=True, blank=True, help_text="Type of the affected object")
    details = models.TextField(blank=True, null=True, help_text="Additional details about the action")
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True, help_text="When this action occurred")
    
    class Meta:
        verbose_name = "Activity Log"
        verbose_name_plural = "Activity Logs"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['user', 'action']),
            models.Index(fields=['object_type', 'object_id']),
        ]
    
    def __str__(self):
        """String representation of the model."""
        return f"{self.get_action_display()} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


class APIKey(models.Model):
    """
    API keys for programmatic access to the URL shortener.
    """
    key = models.CharField(max_length=64, unique=True, db_index=True, help_text="API key value")
    name = models.CharField(max_length=100, help_text="Name of this API key")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='api_keys',
        help_text="User who owns this API key"
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="When this API key was created")
    last_used = models.DateTimeField(null=True, blank=True, help_text="When this API key was last used")
    is_active = models.BooleanField(default=True, help_text="Whether this API key is active")
    permissions = models.TextField(default="read,create", help_text="Comma-separated list of permissions")
    rate_limit = models.PositiveIntegerField(default=100, help_text="Maximum requests per minute")
    
    class Meta:
        verbose_name = "API Key"
        verbose_name_plural = "API Keys"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['key']),
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        """String representation of the model."""
        return f"{self.name} ({self.key[:8]}...)"
    
    def has_permission(self, permission):
        """Check if this API key has a specific permission."""
        return permission in self.permissions.split(',')
    
    def update_last_used(self):
        """Update the last used timestamp."""
        self.last_used = timezone.now()
        self.save(update_fields=['last_used'])
    
    @classmethod
    def generate_key(cls):
        """Generate a new API key."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=64))


class QRCode(models.Model):
    """
    QR codes generated for shortened URLs.
    """
    url = models.ForeignKey(
        ShortenedURL, 
        on_delete=models.CASCADE, 
        related_name='qr_codes',
        help_text="The shortened URL this QR code is for"
    )
    image = models.ImageField(upload_to='qr_codes/', help_text="The QR code image")
    created_at = models.DateTimeField(auto_now_add=True, help_text="When this QR code was created")
    foreground_color = models.CharField(max_length=7, default="#000000", help_text="Foreground color of the QR code")
    background_color = models.CharField(max_length=7, default="#FFFFFF", help_text="Background color of the QR code")
    size = models.PositiveIntegerField(default=200, help_text="Size of the QR code in pixels")
    
    class Meta:
        verbose_name = "QR Code"
        verbose_name_plural = "QR Codes"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['url', 'created_at']),
        ]
    
    def __str__(self):
        """String representation of the model."""
        return f"QR for {self.url.short_code} ({self.size}px)"


# Deprecated models - kept for backwards compatibility
class URL(models.Model):
    """
    Legacy URL model for backwards compatibility.
    """
    original_url = models.URLField(max_length=2000)
    short_code = models.CharField(max_length=100, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    clicks = models.PositiveIntegerField(default=0)
    url_hash = models.CharField(max_length=64, db_index=True, null=True)
    created_by_ip = models.GenericIPAddressField(default='0.0.0.0')
    last_checked = models.DateTimeField(default=timezone.now)
    is_malicious = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Legacy URL"
        verbose_name_plural = "Legacy URLs"
    
    def __str__(self):
        return self.original_url
    
    def save(self, *args, **kwargs):
        if not self.short_code:
            self.short_code = self.generate_unique_code()
        super().save(*args, **kwargs)
    
    def generate_unique_code(self):
        while True:
            code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
            if not URL.objects.filter(short_code=code).exists():
                return code
            

class Link(models.Model):
    original_url = models.URLField(max_length=2000)
    short_code = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    clicks = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.original_url