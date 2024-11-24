from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import URL

class StaticViewSitemap(Sitemap):
    priority = 0.9
    changefreq = 'daily'

    def items(self):
        return ['home', 'contact', 'privacy', 'terms']

    def location(self, item):
        return reverse(item)

class LinkSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return URL.objects.all()

    def lastmod(self, obj):
        return obj.created_at

    def location(self, obj):
        return f'/short/{obj.short_code}/'