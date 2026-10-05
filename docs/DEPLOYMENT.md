# Netra AI - Production Deployment & Operations Guide

This guide covers production deployment for Netra AI across Ubuntu VPS, Docker Compose, Render, and Railway, with Nginx reverse proxying and SSL/TLS certificate installation.

---

## 1. System Architecture

```text
[ Client Smartphone (PWA / Browser) ]
               │
               ▼  HTTPS (443) / WSS (WebSocket)
      [ Nginx Reverse Proxy ]
               ├─── /static/ ──► WhiteNoise Static Storage
               ├─── /media/  ──► Encrypted Storage (Reports / Models)
               │
               ▼  Reverse Proxy (127.0.0.1:8000)
    [ Daphne ASGI Application Server ]
               ├─── Django 5 REST Framework
               └─── Django Channels (/ws/detect/)
               │
      ┌────────┴────────┐
      ▼                 ▼
[ PostgreSQL ]    [ Redis Message Broker ]
                        ▲
                        ▼
            [ Celery Worker & Beat ]
            (90d purge, aggregations)
```

---

## 2. Environment Variables Checklist (`.env`)

Create your production `.env` file from `.env.example`:

```bash
# Core Settings
DEBUG=False
SECRET_KEY=generate-a-strong-random-50-character-key
ALLOWED_HOSTS=netra.yourdomain.com,www.netra.yourdomain.com
DJANGO_SETTINGS_MODULE=config.settings.prod

# Database (PostgreSQL)
DATABASE_URL=postgres://netra_user:strong_password@postgres:5432/netra_db

# Cache & Message Broker (Redis)
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Security & CORS
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
CORS_ALLOWED_ORIGINS=https://netra.yourdomain.com
```

---

## 3. Docker Compose Production Deployment

Netra includes a production-ready `docker-compose.yml` defining the full service cluster.

```bash
# 1. Build and start containers in the background
docker compose up -d --build

# 2. Run database migrations
docker compose exec web python manage.py migrate

# 3. Collect static files
docker compose exec web python manage.py collectstatic --noinput

# 4. Create an administrator account
docker compose exec web python manage.py createsuperuser

# 5. Verify system health
curl https://netra.yourdomain.com/api/health/
```

---

## 4. Ubuntu 22.04 / 24.04 VPS Setup (Bare Metal / Systemd)

### 4.1 Systemd Daphne Service (`/etc/systemd/system/netra-daphne.service`)
```ini
[Unit]
Description=Netra Daphne ASGI Server
After=network.target redis.service postgresql.service

[Service]
User=www-data
WorkingDirectory=/var/www/netra
EnvironmentFile=/var/www/netra/.env
ExecStart=/var/www/netra/venv/bin/daphne -b 127.0.0.1 -p 8000 config.asgi:application
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### 4.2 Systemd Celery Services
* Worker: `/etc/systemd/system/netra-celery.service` -> `celery -A config worker -l INFO`
* Beat: `/etc/systemd/system/netra-celery-beat.service` -> `celery -A config beat -l INFO`

### 4.3 Nginx Reverse Proxy Configuration (`/etc/nginx/sites-available/netra`)
```nginx
upstream daphne_server {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name netra.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name netra.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/netra.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/netra.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    client_max_body_size 10M;

    # Static Files
    location /static/ {
        alias /var/www/netra/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    # Media Uploads
    location /media/ {
        alias /var/www/netra/media/;
        expires 7d;
    }

    # Daphne ASGI Proxy (HTTP & WebSockets)
    location / {
        proxy_pass http://daphne_server;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

Enable site and install SSL certificate via Let's Encrypt Certbot:
```bash
sudo ln -s /etc/nginx/sites-available/netra /etc/nginx/sites-enabled/
sudo certbot --nginx -d netra.yourdomain.com
sudo systemctl restart nginx netra-daphne
```

---

## 5. Mobile PWA Installation Steps

### Android (Chrome / Edge)
1. Open `https://netra.yourdomain.com` in Chrome.
2. Tap the browser menu (`⋮`) -> **"Add to Home Screen"** or **"Install Netra"**.
3. Open Netra from the home screen for a full-screen, standalone app experience.
4. Allow Camera permission when prompted.

### iPhone (iOS Safari)
1. Open `https://netra.yourdomain.com` in Safari.
2. Tap the Share button (box with upward arrow) -> **"Add to Home Screen"**.
3. Open Netra from the iOS home screen.
4. Tap anywhere to initialize Web Audio, then click **"Start Walking"**.

---

## 6. Pre-Demo Verification Checklist

Before demonstrating Netra to judges or users:
- [ ] **Camera Access**: Confirm device camera opens smoothly without permissions blocks.
- [ ] **Earphones Connected**: Verify directional stereo panning (Left ear vs. Right ear).
- [ ] **Speech Synthesis Unmuted**: Ensure phone volume is above 60% and ring/silent switch is set to ring.
- [ ] **Offline Fallback Ready**: Verify `/demo/` runs without requiring network access.
- [ ] **Health Endpoint**: Confirm `curl -s https://.../api/health/` reports `"status": "healthy"`.
