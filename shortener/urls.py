from django.urls import path
from .views import home, redirect_url
from .views import redirect_url, URLCreateAPIView, dashboard   
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

print("Loading shortener.urls")  # Debug line

urlpatterns = [
    # Main pages
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('qr-generator/', views.qr_generator, name='qr_generator'),
    
    # URL shortening endpoints - provide multiple paths for compatibility
    path('shorten_url/', views.shorten_url, name='shorten_url'),  # Main endpoint - underscore
    path('shorten-url/', views.shorten_url, name='shorten_url_dash'),  # Dash version for backward compatibility
    path('shorten/', views.create_short_url, name='create_short_url'),  # Legacy endpoint
    
    # API endpoints
    path('api/urls/create/', views.URLCreateAPIView.as_view(), name='url-create'),
    path('api/urls/<str:short_code>/', views.URLRetrieveAPIView.as_view(), name='url-retrieve'),
    
    # Static pages
    path('l_d/', views.l_d_view, name='l_d'),
    path('contact/', views.contact_view, name='contact'),
    path('contact/submit/', views.contact_submit, name='contact_submit'),
    path('terms/', views.terms_view, name='terms'),
    path('privacy/', views.privacy_view, name='privacy'),
    
    # SEO
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    
    # Put the catchall pattern LAST - Important!
    path('<str:short_code>/', views.redirect_url, name='redirect-url'),
    path('<str:short_code>', views.redirect_url, name='redirect-url-no-slash'),

]