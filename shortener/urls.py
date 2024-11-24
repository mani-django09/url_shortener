from django.urls import path
from .views import home, redirect_url
from .views import redirect_url, URLCreateAPIView , dashboard   
from .views import URLCreateAPIView, URLRetrieveAPIView
from shortener import views
from .sitemaps import LinkSitemap
from .sitemaps import StaticViewSitemap
from django.views.generic import TemplateView
from django.contrib.sitemaps.views import sitemap


sitemaps = {
    'static': StaticViewSitemap,
    'links': LinkSitemap,
}


print("Loading shortener.urls")  # Add this line at the top of your shortener/urls.py

urlpatterns = [
     path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/urls/create/', views.URLCreateAPIView.as_view(), name='url-create'),
    path('short/<str:short_code>/', views.redirect_url, name='redirect-url'),
    path('api/urls/<str:short_code>/', views.URLRetrieveAPIView.as_view(), name='url-retrieve'),
    path('shorten/', URLCreateAPIView.as_view(), name='shorten_url'),  # API to create short URLs
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, 
         name='django.contrib.sitemaps.views.sitemap'),    path('l_d/', views.l_d_view, name='l_d'),  # Link to the l_d.html file
    path('contact/', views.contact_view, name='contact'),
    path('contact/submit/', views.contact_submit, name='contact_submit'),
    path('terms/', views.terms_view, name='terms'),
    path('privacy/', views.privacy_view, name='privacy'),
     path('robots.txt',
         TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
         name='robots.txt'),
]
