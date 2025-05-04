# In shortener/admin.py

from django.contrib import admin
from .models import ActivityLog, URL, ShortenedURL, ClickEvent, BlockedDomain, SuspiciousActivity, APIKey, QRCode, Link

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'timestamp', 'user', 'ip_address', 'object_type']
    list_filter = ['action', 'timestamp', 'object_type']
    search_fields = ['user__username', 'ip_address', 'details']

# Register other models
@admin.register(URL)
class URLAdmin(admin.ModelAdmin):
    list_display = ['original_url', 'short_code', 'created_at', 'clicks']
    search_fields = ['original_url', 'short_code']
    list_filter = ['created_at', 'is_malicious']

@admin.register(ShortenedURL)
class ShortenedURLAdmin(admin.ModelAdmin):
    list_display = ['original_url', 'short_code', 'created_at', 'clicks', 'is_active']
    search_fields = ['original_url', 'short_code']
    list_filter = ['created_at', 'is_active', 'is_malicious']

@admin.register(ClickEvent)
class ClickEventAdmin(admin.ModelAdmin):
    list_display = ['url', 'clicked_at', 'ip_address', 'country', 'device_type']
    list_filter = ['clicked_at', 'country', 'device_type', 'browser', 'os']
    search_fields = ['ip_address', 'referrer']

@admin.register(BlockedDomain)
class BlockedDomainAdmin(admin.ModelAdmin):
    list_display = ['domain', 'reason', 'date_added', 'is_regex']
    search_fields = ['domain', 'reason']
    list_filter = ['date_added', 'is_regex']

@admin.register(SuspiciousActivity)
class SuspiciousActivityAdmin(admin.ModelAdmin):
    list_display = ['ip_address', 'activity_type', 'url_attempted', 'timestamp', 'is_blocked']
    list_filter = ['activity_type', 'timestamp', 'is_blocked']
    search_fields = ['ip_address', 'url_attempted']

@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ['name', 'key', 'user', 'created_at', 'is_active']
    list_filter = ['created_at', 'is_active']
    search_fields = ['name', 'user__username']

@admin.register(QRCode)
class QRCodeAdmin(admin.ModelAdmin):
    list_display = ['url', 'created_at', 'size', 'foreground_color', 'background_color']
    list_filter = ['created_at', 'size']

@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = ['original_url', 'short_code', 'created_at', 'clicks']
    search_fields = ['original_url', 'short_code']
    list_filter = ['created_at']