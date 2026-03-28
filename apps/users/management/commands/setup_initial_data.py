"""
Script to run all post-deployment setup tasks
Run after migrations: python manage.py setup_initial_data
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp


class Command(BaseCommand):
    help = 'Run all initial setup tasks for SmartFarming'

    def handle(self, *args, **options):
        self.setup_site()
        self.setup_google_oauth()

    def setup_site(self):
        """Configure the site domain"""
        try:
            site = Site.objects.get_current()
            if site.domain == 'example.com':
                site.domain = 'localhost:8000'
                site.name = 'SmartFarming'
                site.save()
                self.stdout.write(self.style.SUCCESS('✓ Site configured'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Site setup warning: {e}'))

    def setup_google_oauth(self):
        """Setup Google OAuth from environment variables"""
        try:
            client_id = os.getenv('GOOGLE_CLIENT_ID')
            client_secret = os.getenv('GOOGLE_CLIENT_SECRET')

            if not client_id or not client_secret:
                self.stdout.write(
                    self.style.WARNING('⚠ Google OAuth credentials not in .env')
                )
                return

            google_app, created = SocialApp.objects.get_or_create(
                provider='google',
                defaults={
                    'name': 'Google',
                    'client_id': client_id,
                    'secret': client_secret,
                }
            )

            if not created:
                google_app.client_id = client_id
                google_app.secret = client_secret
                google_app.save()

            current_site = Site.objects.get_current()
            if current_site not in google_app.sites.all():
                google_app.sites.add(current_site)

            status = 'Updated' if not created else 'Created'
            self.stdout.write(
                self.style.SUCCESS(f'✓ {status} Google OAuth app')
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'OAuth setup error: {e}'))
