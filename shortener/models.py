from django.db import models
import string
import random

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
