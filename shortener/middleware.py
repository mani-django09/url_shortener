
import re
from django.http import HttpResponseForbidden
from django.conf import settings

class SecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        if request.method == 'POST' and 'original_url' in request.POST:
            url = request.POST['original_url'].lower()
            
            # Check for suspicious patterns
            patterns = [
                r'seb\.',
                r'bank',
                r'secure.*login',
                r'verify.*account',
                r'password.*reset',
                r'update.*account',
                r'paypal.*confirm',
                r'apple.*verify',
                r'microsoft.*login',
                r'facebook.*security',
                r'\.ru/.*\.(exe|zip|js)$',
                r'cracked.*password',
                r'free.*software.*\.(exe|zip)$'
            ]
            
            for pattern in patterns:
                if re.search(pattern, url):
                    return HttpResponseForbidden('URL blocked for security reasons')
        
        return self.get_response(request)