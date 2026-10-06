"""
Post-migration signals for Netra Accounts.
Automatically ensures default administrator and assistive demo user accounts exist
on fresh deployments (Render, Railway, Docker, SQLite reset) so users can immediately log in.
"""
import logging
from django.db.models.signals import post_migrate
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_migrate)
def ensure_default_accounts(sender, **kwargs):
    """
    Ensures default 'admin' and 'demo' users exist after migrations run.
    Safe for production: if user already exists, it is left untouched.
    """
    # Only run once for the accounts app
    if sender.name != 'apps.accounts':
        return

    from django.contrib.auth.models import User
    from apps.accounts.models import UserSettings

    try:
        # 1. Ensure Superuser 'admin' exists
        admin_user = User.objects.filter(username__iexact='admin').first() or User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@netra-ai.org',
                password='admin123'
            )
            admin_user.first_name = 'Netra'
            admin_user.last_name = 'Admin'
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.save()
            UserSettings.objects.get_or_create(user=admin_user)
            logger.info("Default admin user 'admin' created with password 'admin123'.")

        # 2. Ensure Standard Demo User 'demo' exists
        demo_user = User.objects.filter(username__iexact='demo').first()
        if not demo_user:
            demo_user = User.objects.create_user(
                username='demo',
                email='demo@netra-ai.org',
                password='demo123'
            )
            demo_user.first_name = 'Assistive'
            demo_user.last_name = 'Demo User'
            demo_user.save()
            UserSettings.objects.get_or_create(user=demo_user)
            logger.info("Default demo user 'demo' created with password 'demo123'.")
    except Exception as e:
        logger.warning(f"Could not auto-seed default accounts: {e}")
