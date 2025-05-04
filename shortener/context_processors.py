from django.conf import settings

def google_analytics(request):
    return {
        'GOOGLE_ANALYTICS_ID': settings.GOOGLE_ANALYTICS_ID,
    }


def meta_tags(request):
    """
    Context processor for dynamic meta tags
    This provides meta tag values for all templates
    """
    if hasattr(request, 'current_meta'):
        return {'meta': request.current_meta}
    # Default meta values for homepage
    if request.path == '/':
        meta = {
            'title': 'Bitly - Free URL Shortener | Create & Track Short Links',
            'description': 'Shorten long URLs instantly with Bitly. Create branded short links, track clicks, and optimize your marketing campaigns with powerful analytics.',
            'keywords': 'url shortener, bitly, link shortener, short url, link management, url tracking, custom links',
            'og_title': 'Bitly - Free URL Shortener | Create & Track Short Links',
            'og_description': 'Transform long URLs into memorable short links with Bitly. Track clicks, analyze traffic, and boost your marketing performance.',
            'twitter_title': 'Bitly - Free URL Shortener | Create & Track Short Links',
            'twitter_description': 'Create shortened URLs that are easy to share. Track clicks and optimize your links with Bitly URL Shortener.',
        }
    # Values for QR code page
    elif 'qr-code' in request.path:
        meta = {
            'title': 'Free QR Code Generator | Create Custom QR Codes - Bitly',
            'description': 'Generate free QR codes instantly from any URL. Create customized QR codes for your business, events, or personal use with our easy-to-use generator.',
            'keywords': 'qr code generator, free qr code, custom qr code, url to qr code, qr code maker, qr code from link',
            'og_title': 'Free QR Code Generator | Create Custom QR Codes',
            'og_description': 'Turn any URL into a scannable QR code instantly. Create, customize, and download high-quality QR codes for free.',
            'twitter_title': 'Free QR Code Generator | Bitly',
            'twitter_description': 'Generate QR codes from URLs instantly. Free, customizable, and ready to download.',
        }
    # Values for analytics page
    elif 'analytics' in request.path:
        meta = {
            'title': 'URL Analytics & Click Tracking | Bitly Link Management',
            'description': 'Get detailed insights on your shortened URLs. Track clicks, analyze geographic data, and optimize your link performance with Bitly analytics.',
            'keywords': 'url analytics, link tracking, click stats, url click counter, link performance, traffic analysis',
            'og_title': 'URL Analytics & Click Tracking Dashboard | Bitly',
            'og_description': 'Monitor and analyze your link performance with Bitly\'s comprehensive analytics dashboard. Make data-driven decisions with real-time click data.',
            'twitter_title': 'URL Analytics & Link Tracking | Bitly',
            'twitter_description': 'Track link performance and understand your audience with detailed click analytics.',
        }
    # Values for features page
    elif 'features' in request.path:
        meta = {
            'title': 'URL Shortener Features | Bitly Link Management Platform',
            'description': 'Discover Bitly\'s powerful link management features. Custom URLs, click analytics, QR codes, API access, and more - all for free.',
            'keywords': 'url shortener features, link management, custom short links, click tracking, qr code generator, api access',
            'og_title': 'URL Shortener Features | Bitly Link Management Platform',
            'og_description': 'Explore the powerful features behind Bitly\'s URL shortener and link management platform. More than just a link shortener.',
            'twitter_title': 'URL Shortener Features | Bitly',
            'twitter_description': 'Custom short links, analytics, QR codes, and more. Discover what makes Bitly the best URL shortener.',
        }
    # Default values for any other page
    else:
        meta = {
            'title': 'Bitly URL Shortener | Professional Link Management',
            'description': 'Create short links, custom branded URLs, and QR codes. Track and manage all your links in one place with our professional URL shortener.',
            'keywords': 'url shortener, link management, short url, bit.ly, link tracking, branded links, url analytics',
            'og_title': 'Bitly URL Shortener | Professional Link Management',
            'og_description': 'Create, track, and optimize your links with the most trusted URL shortener and link management platform.',
            'twitter_title': 'Bitly URL Shortener | Link Management',
            'twitter_description': 'Shorten URLs, track clicks, and manage all your links in one place.',
        }
    
    # Add canonical URL for all pages
    meta['canonical'] = request.build_absolute_uri()
    
    return {'meta': meta}