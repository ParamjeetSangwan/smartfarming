import os
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp


class Command(BaseCommand):
    help = 'Register Google OAuth app from environment variables'

    def handle(self, *args, **options):
        try:
            # Get credentials from .env
            client_id = os.getenv('GOOGLE_CLIENT_ID')
            client_secret = os.getenv('GOOGLE_CLIENT_SECRET')

            if not client_id or not client_secret:
                self.stdout.write(
                    self.style.WARNING('Google OAuth credentials not found in .env')
                )
                return

            # Get or create Google provider
            google_app, created = SocialApp.objects.get_or_create(
                provider='google',
                defaults={
                    'name': 'Google',
                    'client_id': client_id,
                    'secret': client_secret,
                }
            )

            # If app existed but credentials changed, update them
            if not created:
                google_app.client_id = client_id
                google_app.secret = client_secret
                google_app.save()

            # Link to site
            current_site = Site.objects.get_current()
            if current_site not in google_app.sites.all():
                google_app.sites.add(current_site)

            status = 'Updated' if not created else 'Created'
            self.stdout.write(
                self.style.SUCCESS(f'✓ {status} Google OAuth app successfully!')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )
