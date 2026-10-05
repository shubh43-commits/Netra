"""
Blind Assist Navigator - Configuration Package
Exports Celery application instance if Celery is installed.
"""
try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except ImportError:
    # Allows running Django without Celery in minimal local environments
    pass
