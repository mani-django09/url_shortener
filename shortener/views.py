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
from .models import Link
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import send_mail, EmailMessage
from django.views.decorators.http import require_http_methods
import logging
from django.template.loader import render_to_string
from django.utils.timezone import now


logger = logging.getLogger(__name__)

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



def l_d_view(request):
    return render(request, 'shortener/l_d.html')


@require_http_methods(["GET", "POST"])
def contact_view(request):
    if request.method == "POST":
        try:
            # Get form data
            first_name = request.POST.get('firstName')
            last_name = request.POST.get('lastName')
            email = request.POST.get('email')
            subject = request.POST.get('subject')
            message = request.POST.get('message')

            # Compose email message
            email_subject = f'New Contact Form Submission: {subject}'
            email_message = f"""
New Contact Form Submission

From: {first_name} {last_name}
Email: {email}
Subject: {subject}

Message:
{message}
            """

            # Send email
            send_mail(
                subject=email_subject,
                message=email_message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=False,
            )

            # Send confirmation email to user
            confirmation_message = f"""
Dear {first_name},

Thank you for contacting us. We have received your message and will get back to you soon.

Best regards,
URL Shortener Team
            """
            
            send_mail(
                subject='Thank you for contacting us',
                message=confirmation_message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )

            return JsonResponse({
                'status': 'success',
                'message': 'Your message has been sent successfully! We will get back to you soon.'
            })
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'Failed to send message. Error: {str(e)}'
            }, status=500)

    # If GET request, just render the form
    return render(request, 'includes/contact.html')

@csrf_exempt  # Only for testing, remove in production
def contact_submit(request):
    if request.method == 'POST':
        # Get form data
        first_name = request.POST.get('firstName')
        last_name = request.POST.get('lastName')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        try:
            # Email content
            email_body = f"""
            New Contact Form Submission
            
            From: {first_name} {last_name}
            Email: {email}
            Subject: {subject}
            
            Message:
            {message}
            """

            # Send email
            email = EmailMessage(
                f'Contact Form: {subject}',
                email_body,
                'your-email@gmail.com',  # Replace with your email
                ['your-email@gmail.com'],  # Replace with your email
                reply_to=[email]
            )
            email.send()

            return JsonResponse({
                'status': 'success',
                'message': 'Thank you for your message. We will get back to you soon!'
            })
        except Exception as e:
            print(f"Error sending email: {str(e)}")  # For debugging
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
    date = now().strftime('%Y-%m-%d')
    content = render_to_string('sitemap.xml', {'date': date})
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

#def qr_generator(request):
 #   return render(request, 'shortener/qr_generator.html')
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
