from django.shortcuts import render, redirect, get_object_or_404
import random
import string
from .models import URL
from django.http import HttpResponse
from .forms import URLForm
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from .serializers import URLSerializer
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import ActivityLog


CUSTOM_DOMAIN = "bitly.works"


def dashboard(request):
    urls = URL.objects.all().order_by('-created_at')  # Consider adding pagination here
    context = {
        'urls': urls,
    }
    return render(request, 'shortener/dashboard.html', context)

class URLCreateAPIView(generics.CreateAPIView):
    queryset = URL.objects.all()
    serializer_class = URLSerializer

    
    def generate_short_code(self, length=6):
        characters = string.ascii_uppercase + string.ascii_lowercase + string.digits
        while True:
            short_code = ''.join(random.choice(characters) for _ in range(length))
            if not URL.objects.filter(short_code=short_code).exists():  # Check for uniqueness
                return short_code

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            url_instance = serializer.save()
            url_instance.short_code = self.generate_short_code()  # Generate the short code
            url_instance.save()
            short_url = request.build_absolute_uri(f"/short/{url_instance.short_code}/")  # Correct short URL construction
            return Response({'short_url': short_url}, status=status.HTTP_201_CREATED)  # Return short URL
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class URLRetrieveAPIView(generics.RetrieveAPIView):
    queryset = URL.objects.all()
    lookup_field = 'short_code'  # Ensure this matches your URL pattern

    def get(self, request, short_code, *args, **kwargs):
        url_instance = get_object_or_404(URL, short_code=short_code)
        return redirect(url_instance.original_url)  # Redirect to the original URL

def home(request):
    short_url = None
    error_message = None
    if request.method == 'POST':
        form = URLForm(request.POST)
        if form.is_valid():
            url_instance = form.save()
            short_url = request.build_absolute_uri(f"/short/{url_instance.short_code}/")
        else:
            error_message = "Error creating short URL. Please check the URL format and try again."
    else:
        form = URLForm()
    
    return render(request, 'shortener/home.html', {'form': form, 'short_url': short_url, 'error_message': error_message})
def redirect_url(request, short_code):
    url_instance = get_object_or_404(URL, short_code=short_code)
    url_instance.clicks += 1
    url_instance.save()
    return redirect(url_instance.original_url)

@csrf_exempt

def shorten_url(request):
    if request.method == 'POST':
        original_url = request.POST.get('original_url')
        # Logic to create a shortened URL...
        short_url = 'your_short_url_here'  # Example shortened URL
        return JsonResponse({'short_url': short_url})
    return JsonResponse({'error': 'Invalid request'}, status=400)


