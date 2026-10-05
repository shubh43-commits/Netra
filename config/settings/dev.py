"""
Development settings for Netra AI.
Configured for zero-friction local development with SQLite and in-memory or Redis channels.
"""
from .base import *  # noqa: F401, F403
import os

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '[::1]', '*']

# Allow all origins for convenient frontend and mobile debugging in dev
CORS_ALLOW_ALL_ORIGINS = True

# Standard static files storage in dev (disables strict manifest hash requirement)
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Database: SQLite for zero-setup local development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',  # noqa: F405
    }
}

# Channels Layer:
# Uses InMemoryChannelLayer if REDIS_URL is not provided or reachable
REDIS_URL = os.environ.get('REDIS_URL', '')  # noqa: F405

if REDIS_URL:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                'hosts': [REDIS_URL],
            },
        },
    }
else:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} [{name}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
