from django.db import models
import string
import random
from django.utils import timezone

class URL(models.Model):
    ...
    clicks = models.IntegerField(default=0)

class URL(models.Model):
    original_url = models.URLField()
    short_code = models.CharField(max_length=15, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    clicks = models.IntegerField(default=0)

    def __str__(self):
        return self.original_url

    def save(self, *args, **kwargs):
        if not self.short_code:
            self.short_code = self.generate_short_code()
        super().save(*args, **kwargs)

    def generate_short_code(self):
        length = 6
        characters = string.ascii_letters + string.digits
        short_code = ''.join(random.choices(characters, k=length))
        return short_code

class ActivityLog(models.Model):
    original_url = models.URLField()
    short_url = models.URLField()
    short_code = models.CharField(max_length=10, unique=True,default='default_code')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.original_url} -> {self.short_url} at {self.timestamp}"
    

    # shortener/models.py
from django.db import models

class Link(models.Model):
    original_url = models.URLField()  # The original URL before shortening
    shortened_url = models.CharField(max_length=50, unique=True)  # The shortened URL
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp of creation
    updated_at = models.DateTimeField(auto_now=True)  # Timestamp of last update

    def __str__(self):
        return self.original_url

class BlockedDomain(models.Model):
    domain = models.CharField(max_length=255, unique=True)
    reason = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['domain']),
        ]

class SuspiciousActivity(models.Model):
    ip_address = models.GenericIPAddressField()
    url_attempted = models.URLField(max_length=2000)
    user_agent = models.TextField()
    request_data = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['ip_address', 'timestamp']),
        ]

class URL(models.Model):
    original_url = models.URLField(max_length=2000)
    short_code = models.CharField(max_length=10, unique=True, blank=True)  # Make it blank=True
    created_at = models.DateTimeField(auto_now_add=True)
    clicks = models.PositiveIntegerField(default=0)
    url_hash = models.CharField(max_length=64, db_index=True, null=True)  # Add null=True
    created_by_ip = models.GenericIPAddressField(default='0.0.0.0')  # Add default
    last_checked = models.DateTimeField(default=timezone.now)
    is_malicious = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.short_code:
            self.short_code = self.generate_unique_code()
        super().save(*args, **kwargs)

    def generate_unique_code(self):
        while True:
            code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
            if not URL.objects.filter(short_code=code).exists():
                return code