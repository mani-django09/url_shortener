from django.shortcuts import render, redirect, get_object_or_404
import random
import string
import requests
from .models import URL
from django.core.mail.backends.smtp import EmailBackend
import tldextract
from django.http import HttpResponse
from .forms import URLForm
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from .serializers import URLSerializer
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import ActivityLog
from .models import Link
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import send_mail, EmailMessage
from django.views.decorators.http import require_http_methods
import logging
from django.template.loader import render_to_string
from django.utils.timezone import now
import re
from .models import URL, BlockedDomain
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import hashlib
import json
from django.http import JsonResponse
from django.core.cache import cache
from urllib.parse import urlparse
from django.shortcuts import render, get_object_or_404
from datetime import timedelta
from user_agents import parse
import geoip2.database
from django.db.models import Count
from django.utils import timezone
from django.views.decorators.cache import cache_page
from .models import Link
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie

logger = logging.getLogger(__name__)

CUSTOM_DOMAIN = "bitly.works"

def dashboard(request):
    urls = URL.objects.all().order_by('-created_at')
    context = {
        'urls': urls,
    }
    return render(request, 'shortener/dashboard.html', context)

# Success page view - NEW
def success_view(request, short_code):
    """Display success page after URL shortening"""
    try:
        url_instance = get_object_or_404(URL, short_code=short_code)
        short_url = request.build_absolute_uri(f'/{short_code}')
        
        # Force HTTPS
        short_url = short_url.replace("http://", "https://")
        
        context = {
            'short_code': short_code,
            'short_url': short_url,
            'original_url': url_instance.original_url,
            'clicks': url_instance.clicks,
            'created_at': url_instance.created_at,
        }
        return render(request, 'shortener/success.html', context)
    except URL.DoesNotExist:
        return redirect('home')

class URLCreateAPIView(generics.CreateAPIView):
    queryset = URL.objects.all()
    serializer_class = URLSerializer

    def generate_short_code(self, length=6):
        characters = string.ascii_uppercase + string.ascii_lowercase + string.digits
        while True:
            short_code = ''.join(random.choice(characters) for _ in range(length))
            if not URL.objects.filter(short_code=short_code).exists():
                return short_code

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            url_instance = serializer.save()
            url_instance.short_code = self.generate_short_code()
            url_instance.save()
            short_url = request.build_absolute_uri(f"/{url_instance.short_code}/")
            return Response({'short_url': short_url}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class URLRetrieveAPIView(generics.RetrieveAPIView):
    queryset = URL.objects.all()
    lookup_field = 'short_code'

    def get(self, request, short_code, *args, **kwargs):
        url_instance = get_object_or_404(URL, short_code=short_code)
        return redirect(url_instance.original_url)

@cache_page(60 * 15)
@ensure_csrf_cookie
def home(request):
    short_url = None
    error_message = None
    if request.method == 'POST':
        form = URLForm(request.POST)
        if form.is_valid():
            url_instance = form.save()
            short_url = request.build_absolute_uri(f"/{url_instance.short_code}/")
        else:
            error_message = "Error creating short URL. Please check the URL format and try again."
    else:
        form = URLForm()
    
    return render(request, 'shortener/home.html', {'form': form, 'short_url': short_url, 'error_message': error_message})

def redirect_url(request, short_code):
    """View for redirecting short URLs"""
    logger.info(f"Processing redirect for short code: {short_code}")
    
    try:
        url_instance = URL.objects.get(short_code__iexact=short_code)
        
        # Update click count
        url_instance.clicks += 1
        url_instance.save()
        
        # Record analytics if available
        try:
            ActivityLog.objects.create(
                original_url=url_instance.original_url,
                short_url=request.build_absolute_uri(),
                short_code=short_code,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                referer=request.META.get('HTTP_REFERER', '')
            )
        except Exception as e:
            logger.error(f"Error recording analytics: {str(e)}")
        
        return redirect(url_instance.original_url)
        
    except URL.DoesNotExist:
        logger.error(f"Short code not found: {short_code}")
        return HttpResponse(f"The shortened URL '{short_code}' was not found.", status=404)
    except Exception as e:
        logger.error(f"Error in redirect_url: {str(e)}")
        return HttpResponse("An error occurred. Please try again later.", status=500)

@csrf_protect  
def shorten_url(request):
    """View function to create shortened URLs - Updated to support both AJAX and form submission"""
    if request.method == 'POST':
        original_url = request.POST.get('original_url')
        
        # Basic URL validation
        if not original_url:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'URL is required'}, status=400)
            return redirect('home')
        
        # Add https:// if missing
        if not original_url.startswith(('http://', 'https://')):
            original_url = 'https://' + original_url
        
        try:
            # Validate URL
            is_valid, cleaned_url = clean_and_validate_url(original_url)
            if not is_valid:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': 'Invalid URL format'}, status=400)
                return redirect('home')
            
            original_url = cleaned_url
            
            # Check if URL already exists in database
            url_hash = hashlib.sha256(original_url.encode()).hexdigest()
            existing_url = URL.objects.filter(url_hash=url_hash).first()
            
            if existing_url:
                short_code = existing_url.short_code
            else:
                # Create new shortened URL
                url_instance = URL.objects.create(
                    original_url=original_url,
                    short_code=generate_unique_code(),
                    url_hash=url_hash,
                    created_by_ip=get_client_ip(request)
                )
                short_code = url_instance.short_code
            
            # Build short URL
            short_url = request.build_absolute_uri(f'/{short_code}')
            short_url = short_url.replace("http://", "https://")
            
            # Check if it's an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'short_url': short_url,
                    'short_code': short_code,
                    'original_url': original_url
                })
            else:
                # Redirect to success page for form submissions
                return redirect('success', short_code=short_code)

        except Exception as e:
            logger.error(f"Error creating short URL: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Error creating shortened URL'}, status=500)
            return redirect('home')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    return redirect('home')

def l_d_view(request):
    return render(request, 'shortener/l_d.html')

@require_http_methods(["GET", "POST"])
def contact_view(request):
    if request.method == "POST":
        try:
            email_backend = EmailBackend(
                host=settings.EMAIL_HOST,
                port=settings.EMAIL_PORT,
                username=settings.EMAIL_HOST_USER,
                password=settings.EMAIL_HOST_PASSWORD,
                use_tls=settings.EMAIL_USE_TLS,
                fail_silently=False,
                timeout=30
            )

            first_name = request.POST.get('firstName')
            last_name = request.POST.get('lastName')
            email = request.POST.get('email')
            subject = request.POST.get('subject')
            message = request.POST.get('message')

            email_subject = f'New Contact Form Submission: {subject}'
            email_message = f"""
New Contact Form Submission

From: {first_name} {last_name}
Email: {email}
Subject: {subject}

Message:
{message}
            """

            main_email = EmailMessage(
                subject=email_subject,
                body=email_message,
                from_email=settings.EMAIL_HOST_USER,
                to=[settings.ADMIN_EMAIL],
                connection=email_backend
            )
            main_email.send()

            confirmation_message = f"""
Dear {first_name},

Thank you for contacting us. We have received your message and will get back to you soon.

Best regards,
URL Shortener Team
            """

            confirmation_email = EmailMessage(
                subject='Thank you for contacting us',
                body=confirmation_message,
                from_email=settings.EMAIL_HOST_USER,
                to=[email],
                connection=email_backend
            )
            confirmation_email.send()

            return JsonResponse({
                'status': 'success',
                'message': 'Your message has been sent successfully!'
            })

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'Failed to send message. Please try again later.'
            }, status=500)

    return render(request, 'includes/contact.html')

@csrf_exempt
def contact_submit(request):
    if request.method == 'POST':
        first_name = request.POST.get('firstName')
        last_name = request.POST.get('lastName')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        try:
            email_body = f"""
            New Contact Form Submission
            
            From: {first_name} {last_name}
            Email: {email}
            Subject: {subject}
            
            Message:
            {message}
            """

            email = EmailMessage(
                f'Contact Form: {subject}',
                email_body,
                'your-email@gmail.com',
                ['your-email@gmail.com'],
                reply_to=[email]
            )
            email.send()

            return JsonResponse({
                'status': 'success',
                'message': 'Thank you for your message. We will get back to you soon!'
            })
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'Sorry, there was an error sending your message.'
            }, status=500)

    return JsonResponse({'message': 'Invalid request method'}, status=400)

def terms_view(request):
    return render(request, 'includes/terms.html')

def privacy_view(request):
    return render(request, 'includes/privacy.html')

def sitemap_view(request):
    """Generate the sitemap.xml file"""
    current_date = now()
    content = render_to_string('sitemap.xml', {
        'date': current_date,
    })
    return HttpResponse(content, content_type='application/xml')

def robots_txt(request):
    """Generate the robots.txt file"""
    host = request.get_host()
    content = f"""User-agent: *
Allow: /
Disallow: /admin/

# Sitemap
Sitemap: http://{host}/sitemap.xml
"""
    return HttpResponse(content, content_type='text/plain')

def qr_generator(request):
    context = {
        'faqs': [
            {
                'question': 'What is a QR Code?',
                'answer': 'A QR Code is a two-dimensional barcode that can be quickly read by digital devices such as smartphones.'
            },
            {
                'question': 'What types of QR codes can I create?',
                'answer': 'You can create QR codes for URLs, text, contact information, phone numbers, SMS, emails, and more.'
            },
            {
                'question': 'Are the QR codes free to use?',
                'answer': 'Yes, all QR codes generated on our platform are free to use for both personal and commercial purposes.'
            },
            {
                'question': 'What is the best size for a QR code?',
                'answer': 'The recommended size depends on your use case. For print materials, we recommend at least 300x300 pixels.'
            },
            {
                'question': 'Can I customize my QR code?',
                'answer': 'Yes, you can customize the color, size, and error correction level of your QR code.'
            },
        ],
        'stats': {
            'total_generated': 1000000,
            'total_scans': 5000000,
            'active_users': 100000,
        }
    }
    return render(request, 'shortener/qr_generator.html', context)

# Analytics view for success page - NEW
def analytics_dashboard(request, short_code):
    """Display analytics for a specific shortened URL"""
    try:
        url_instance = get_object_or_404(URL, short_code=short_code)
        
        # Get click analytics
        recent_clicks = ActivityLog.objects.filter(short_code=short_code).order_by('-timestamp')[:50]
        
        context = {
            'url': url_instance,
            'recent_clicks': recent_clicks,
            'total_clicks': url_instance.clicks,
        }
        return render(request, 'shortener/analytics.html', context)
    except URL.DoesNotExist:
        return redirect('home')

class SecurityChecks:
    @staticmethod
    def is_valid_url(url):
        """Enhanced URL validation - FIXED VERSION"""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        url = url.strip()
        
        url_pattern = re.compile(
            r'^(https?:\/\/)?' +
            r'((([a-z\d]([a-z\d-]*[a-z\d])*)\.)+[a-z]{2,}|' +
            r'((\d{1,3}\.){3}\d{1,3}))' +
            r'(\:\d+)?(\/[-a-z\d%_.~+]*)*' +
            r'(\?[;&a-z\d%_.~+=-]*)?' +
            r'(\#[-a-z\d_]*)?$',
            re.IGNORECASE
        )
        
        # FIXED: Always return a tuple (bool, url)
        if not url_pattern.match(url):
            return False, url
            
        try:
            URLValidator()(url)
            return True, url
        except ValidationError:
            return False, url

def clean_and_validate_url(url):
    """Helper function to clean and validate a URL"""
    url = url.strip() if url else ""
    
    if url and not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    is_valid, url = SecurityChecks.is_valid_url(url)
    return is_valid, url

    @staticmethod
    def check_phishing_database(url):
        api_key = settings.SAFE_BROWSING_API_KEY
        api_url = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
        
        payload = {
            "client": {
                "clientId": "your-client-id",
                "clientVersion": "1.0.0"
            },
            "threatInfo": {
                "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE"],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": url}]
            }
        }
        
        headers = {"Content-Type": "application/json"}
        response = requests.post(api_url, params={"key": api_key}, json=payload, headers=headers)
        
        return len(response.json().get("matches", [])) == 0

    @staticmethod
    def check_domain_reputation(domain):
        cache_key = f'domain_reputation_{domain}'
        reputation = cache.get(cache_key)
        
        if reputation is None:
            blocked = BlockedDomain.objects.filter(domain=domain).exists()
            reputation = not blocked
            cache.set(cache_key, reputation, 3600)
        
        return reputation

    @staticmethod
    def detect_suspicious_patterns(url):
        suspicious_patterns = [
            r'bank', r'login', r'secure', r'account', r'verify', r'seb\.',
            r'paypal', r'signin', r'security', r'password', r'update'
        ]
        
        url_lower = url.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, url_lower):
                return True
        return False

def generate_unique_code():
    """Generate a unique short code"""
    while True:
        code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        if not URL.objects.filter(short_code=code).exists():
            return code

@csrf_exempt
def create_short_url(request):
    """Alternative endpoint for creating short URLs"""
    if request.method == 'POST':
        original_url = request.POST.get('original_url')
        
        is_valid, cleaned_url = clean_and_validate_url(original_url)
        if not is_valid:
            return JsonResponse({'error': 'Invalid URL format'}, status=400)

        try:
            url_hash = hashlib.sha256(cleaned_url.encode()).hexdigest()
            existing_url = URL.objects.filter(url_hash=url_hash).first()
            
            if existing_url:
                url = request.build_absolute_uri(f'/{existing_url.short_code}')
                url = url.replace("http://", "https://")
                return JsonResponse({'short_url': url})

            url_instance = URL.objects.create(
                original_url=cleaned_url,
                short_code=generate_unique_code(),
                url_hash=url_hash,
                created_by_ip=get_client_ip(request)
            )
            
            url = request.build_absolute_uri(f'/{url_instance.short_code}')
            url = url.replace("http://", "https://")
            return JsonResponse({'short_url': url})

        except Exception as e:
            logger.error(f"Error creating short URL: {str(e)}")
            return JsonResponse({'error': 'Error creating shortened URL'}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_client_ip(request):
    """Get the client's IP address from request headers"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def log_suspicious_activity(request, url):
    from .models import SuspiciousActivity
    SuspiciousActivity.objects.create(
        ip_address=get_client_ip(request),
        url_attempted=url,
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        request_data=json.dumps(dict(request.POST))
    )

def record_click(request, url_instance):
    try:
        url_instance.clicks += 1
        url_instance.save()
        
        ActivityLog.objects.create(
            url=url_instance,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            referer=request.META.get('HTTP_REFERER', '')
        )
    except Exception as e:
        logger.error(f"Error recording click: {str(e)}")

def redirect_view(request, short_code):
    """View for redirecting short URLs"""
    try:
        url_obj = URL.objects.get(short_code=short_code)
        
        request.current_meta = {
            'title': f'{short_code} - Bitly URL Redirect',
            'description': f'This shortened URL redirects to a destination selected by the creator. Created with Bitly URL Shortener.',
            'keywords': 'shortened url, redirect, bitly, short link',
            'og_title': f'Shortened URL: {short_code}',
            'og_description': 'Click to visit the destination of this shortened URL.',
            'twitter_title': f'Shortened URL: {short_code}',
            'twitter_description': 'Click to visit the destination of this shortened URL.',
            'canonical': request.build_absolute_uri(),
        }
        
        url_obj.clicks += 1
        url_obj.save()
        
        return redirect(url_obj.original_url)
    except URL.DoesNotExist:
        return render(request, 'shortener/not_found.html', status=404)