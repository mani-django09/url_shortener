# shortener/management/commands/setup_site.py
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site

class Command(BaseCommand):
    help = 'Setup default site'

    def handle(self, *args, **kwargs):
        # Update or create the default site
        Site.objects.update_or_create(
            id=1,
            defaults={
                'domain': 'bitly.works',
                'name': 'Bitly URL Shortener'
            }
        )
        self.stdout.write(self.style.SUCCESS('Successfully set up site'))