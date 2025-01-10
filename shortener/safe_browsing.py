
import requests
from django.conf import settings
from django.core.cache import cache
import hashlib
import logging

logger = logging.getLogger(__name__)

class SafeBrowsingAPI:
    def __init__(self):
        self.api_key = settings.SAFE_BROWSING_API_KEY
        self.config = settings.SAFE_BROWSING_CONFIG
        self.rate_limit = settings.SAFE_BROWSING_RATE_LIMIT

    def check_url(self, url):
        """Check if URL is safe using Google Safe Browsing API"""
        # Check cache first
        cache_key = f'safebrowsing_{hashlib.sha256(url.encode()).hexdigest()}'
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        try:
            payload = {
                "client": {
                    "clientId": settings.SAFE_BROWSING_CLIENT_ID,
                    "clientVersion": settings.SAFE_BROWSING_CLIENT_VERSION
                },
                "threatInfo": {
                    "threatTypes": self.config['THREAT_TYPES'],
                    "platformTypes": self.config['PLATFORM_TYPES'],
                    "threatEntryTypes": self.config['THREAT_ENTRY_TYPES'],
                    "threatEntries": [{"url": url}]
                }
            }

            response = requests.post(
                self.config['API_ENDPOINT'],
                params={"key": self.api_key},
                json=payload,
                timeout=self.config['REQUEST_TIMEOUT']
            )
            response.raise_for_status()

            # Process response
            result = response.json()
            is_safe = "matches" not in result
            
            # Cache the result
            cache.set(cache_key, is_safe, self.config['MAX_CACHE_TIME'])
            
            return is_safe

        except requests.exceptions.RequestException as e:
            logger.error(f"Safe Browsing API error: {str(e)}")
            # If API fails, err on the side of caution
            return False

    def is_rate_limited(self):
        """Check if we've exceeded rate limits"""
        current_minute = cache.get('safebrowsing_current_minute', 0)
        current_day = cache.get('safebrowsing_current_day', 0)

        return (current_minute >= self.rate_limit['MAX_REQUESTS_PER_MINUTE'] or 
                current_day >= self.rate_limit['MAX_REQUESTS_PER_DAY'])

    def increment_rate_counters(self):
        """Increment rate limiting counters"""
        cache.incr('safebrowsing_current_minute', 1)
        cache.incr('safebrowsing_current_day', 1)