from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.http import HttpResponse


def ads_txt_view(request):
    """Serve ads.txt file"""
    content = "google.com, pub-6913093595582462, DIRECT, f08c47fec0942fa0"
    return HttpResponse(content, content_type='text/plain')

def robots_txt_view(request):
    """Serve robots.txt file"""
    lines = [
        "User-agent: *",
        "Allow: /",
        "Sitemap: https://bitly.works/sitemap.xml",
        "",
        "# Google AdSense",
        "User-agent: Mediapartners-Google",
        "Allow: /",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


urlpatterns = [
    path('admin/', admin.site.urls),
      path('ads.txt', ads_txt_view, name='ads_txt'),
        path('', include('shortener.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

