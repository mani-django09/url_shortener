from django.urls import path
from .views import home, redirect_url
from .views import redirect_url, URLCreateAPIView , dashboard   
from .views import URLCreateAPIView, URLRetrieveAPIView
from shortener import views


print("Loading shortener.urls")  # Add this line at the top of your shortener/urls.py

urlpatterns = [
     path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/urls/create/', views.URLCreateAPIView.as_view(), name='url-create'),
    path('short/<str:short_code>/', views.redirect_url, name='redirect-url'),
    path('api/urls/<str:short_code>/', views.URLRetrieveAPIView.as_view(), name='url-retrieve'),
    path('shorten/', URLCreateAPIView.as_view(), name='shorten_url'),  # API to create short URLs

]

