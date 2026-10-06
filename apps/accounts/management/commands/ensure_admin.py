"""
Django Management Command: ensure_admin
Creates or verifies default 'admin' and 'demo' accounts for production deployments.
Usage:
    python manage.py ensure_admin
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.accounts.models import UserSettings


class Command(BaseCommand):
    help = "Ensures default admin and demo user accounts exist with functional credentials."

    def handle(self, *args, **options):
        admin_username = os.environ.get("ADMIN_USERNAME", "admin")
        admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
        admin_email = os.environ.get("ADMIN_EMAIL", "admin@netra-ai.org")

        demo_username = os.environ.get("DEMO_USERNAME", "demo")
        demo_password = os.environ.get("DEMO_PASSWORD", "demo123")
        demo_email = os.environ.get("DEMO_EMAIL", "demo@netra-ai.org")

        # 1. Superuser
        admin_user = User.objects.filter(username__iexact=admin_username).first() or User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.create_superuser(
                username=admin_username,
                email=admin_email,
                password=admin_password
            )
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.save()
            UserSettings.objects.get_or_create(user=admin_user)
            self.stdout.write(self.style.SUCCESS(f"Created superuser '{admin_username}' with password '{admin_password}'"))
        else:
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.set_password(admin_password)
            admin_user.save()
            UserSettings.objects.get_or_create(user=admin_user)
            self.stdout.write(self.style.SUCCESS(f"Updated superuser '{admin_user.username}' with active password '{admin_password}'"))

        # 2. Demo User
        demo_user = User.objects.filter(username__iexact=demo_username).first()
        if not demo_user:
            demo_user = User.objects.create_user(
                username=demo_username,
                email=demo_email,
                password=demo_password
            )
            demo_user.save()
            UserSettings.objects.get_or_create(user=demo_user)
            self.stdout.write(self.style.SUCCESS(f"Created demo user '{demo_username}' with password '{demo_password}'"))
        else:
            demo_user.set_password(demo_password)
            demo_user.save()
            UserSettings.objects.get_or_create(user=demo_user)
            self.stdout.write(self.style.SUCCESS(f"Updated demo user '{demo_user.username}' password"))
