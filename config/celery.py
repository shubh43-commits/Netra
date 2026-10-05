"""
Celery configuration for Netra AI.
Provides asynchronous worker support and scheduled jobs (Celery beat) for:
- Feedback frame retention cleanup (90 days)
- Analytics daily summary aggregations
- Long-running OCR and scene description tasks
"""
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

app = Celery('netra')

# Load task configuration from Django settings with CELERY_ namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover asynchronous tasks in all installed apps
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Simple debug task to verify Celery broker and worker connectivity."""
    print(f'Celery Request: {self.request!r}')
