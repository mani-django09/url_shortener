from django.contrib import admin
from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('original_url', 'short_url', 'timestamp')
    search_fields = ('original_url', 'short_url')
    list_filter = ('timestamp',)