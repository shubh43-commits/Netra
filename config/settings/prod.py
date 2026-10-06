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
    ALLOWED_HOSTS = ['*']

# Dynamically ensure Render / Railway / Cloud domains are allowed
render_host = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if render_host and render_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_host)

railway_host = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
if railway_host and railway_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(railway_host)

if '*' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.extend(['.onrender.com', '.railway.app', '.up.railway.app', 'localhost', '127.0.0.1'])

# CORS settings for production
CORS_ALLOW_ALL_ORIGINS = os.environ.get('CORS_ALLOW_ALL_ORIGINS', 'True').lower() == 'true'
cors_origins_raw = os.environ.get('CORS_ALLOWED_ORIGINS', '')
if cors_origins_raw:
    CORS_ALLOWED_ORIGINS = [orig.strip() for orig in cors_origins_raw.split(',') if orig.strip()]
else:
    CORS_ALLOWED_ORIGINS = [
        'https://*.onrender.com',
        'http://*.onrender.com',
        'https://*.railway.app',
        'http://*.railway.app',
    ]


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

# Production Security Headers & SSL
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# Only enforce SSL redirect if explicitly configured or running on known HTTPS cloud platform
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'False').lower() == 'true'

# Cookie Security & SameSite (Lax ensures cross-origin navigation & POST preservation)
SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true' or SECURE_SSL_REDIRECT
CSRF_COOKIE_SECURE = os.environ.get('CSRF_COOKIE_SECURE', 'False').lower() == 'true' or SECURE_SSL_REDIRECT
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = False

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Comprehensive CSRF Trusted Origins for Cloud Deployments
CSRF_TRUSTED_ORIGINS = [
    'https://*.onrender.com',
    'http://*.onrender.com',
    'https://*.railway.app',
    'http://*.railway.app',
    'https://*.up.railway.app',
    'http://*.up.railway.app',
    'https://*.vercel.app',
    'https://*.fly.dev',
    'https://*.run.app',
    'https://*.appspot.com',
    'https://*.herokuapp.com',
    'http://127.0.0.1:8000',
    'http://localhost:8000',
    'http://127.0.0.1',
    'http://localhost',
]

csrf_trusted_raw = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
if csrf_trusted_raw:
    for orig in csrf_trusted_raw.split(','):
        cleaned = orig.strip()
        if cleaned and cleaned not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(cleaned)

# Automatically add dynamically detected cloud hostnames
if render_host:
    for scheme in ('https://', 'http://'):
        h_url = f"{scheme}{render_host}"
        if h_url not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(h_url)

render_url = os.environ.get('RENDER_EXTERNAL_URL')
if render_url and render_url not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append(render_url)

if railway_host:
    for scheme in ('https://', 'http://'):
        h_url = f"{scheme}{railway_host}"
        if h_url not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(h_url)

# Add any custom domain from ALLOWED_HOSTS into CSRF_TRUSTED_ORIGINS
for h in ALLOWED_HOSTS:
    if h not in ('*', '.onrender.com', '.railway.app', '.up.railway.app'):
        clean = h.lstrip('.')
        for scheme in ('https://', 'http://'):
            cand = f"{scheme}{clean}"
            if cand not in CSRF_TRUSTED_ORIGINS:
                CSRF_TRUSTED_ORIGINS.append(cand)

