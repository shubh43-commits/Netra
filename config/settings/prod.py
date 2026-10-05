"""
Production settings for Netra AI.
Configured for secure production deployment with PostgreSQL, Redis channels, WhiteNoise, and SSL.
"""
import os
import urllib.parse
from .base import *  # noqa: F401, F403

DEBUG = False

SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable must be set in production!")

allowed_hosts_raw = os.environ.get('ALLOWED_HOSTS', '')
if allowed_hosts_raw:
    ALLOWED_HOSTS = [h.strip() for h in allowed_hosts_raw.split(',') if h.strip()]
else:
    ALLOWED_HOSTS = ['.onrender.com', 'localhost', '127.0.0.1', '*']

# CORS settings for production
CORS_ALLOW_ALL_ORIGINS = os.environ.get('CORS_ALLOW_ALL_ORIGINS', 'True').lower() == 'true'
cors_origins_raw = os.environ.get('CORS_ALLOWED_ORIGINS', '')
if cors_origins_raw:
    CORS_ALLOWED_ORIGINS = [orig.strip() for orig in cors_origins_raw.split(',') if orig.strip()]
else:
    CORS_ALLOWED_ORIGINS = ['https://*.onrender.com']

# Database: PostgreSQL if DATABASE_URL or DB_NAME provided, otherwise fallback to SQLite for free tiers
database_url = os.environ.get('DATABASE_URL', '')
if database_url and (database_url.startswith('postgres://') or database_url.startswith('postgresql://')):
    # Normalize postgres:// to postgresql:// for compatibility
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    parsed = urllib.parse.urlparse(database_url)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': parsed.path.lstrip('/'),
            'USER': parsed.username,
            'PASSWORD': parsed.password,
            'HOST': parsed.hostname,
            'PORT': parsed.port or 5432,
        }
    }
elif os.environ.get('DB_NAME'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'netra_db'),
            'USER': os.environ.get('DB_USER', 'netra_user'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Channels Layer: Redis if REDIS_URL provided, else InMemoryChannelLayer
REDIS_URL = os.environ.get('REDIS_URL', '')
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

# Strict Production Security Headers & SSL
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True').lower() == 'true'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

csrf_trusted_raw = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
if csrf_trusted_raw:
    CSRF_TRUSTED_ORIGINS = [orig.strip() for orig in csrf_trusted_raw.split(',') if orig.strip()]
else:
    CSRF_TRUSTED_ORIGINS = [
        'https://*.onrender.com',
        'http://*.onrender.com',
        'http://127.0.0.1:8000',
        'http://localhost:8000',
    ]
