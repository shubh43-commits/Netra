# ==============================================================================
# Dockerfile - Netra: Your Phone Just Got Eyes
# Production ASGI container powered by Daphne
# ==============================================================================
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies (build tools, libpq for Postgres)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Compile i18n locales and prepare directory structure
RUN python scripts/compile_locales.py && \
    mkdir -p /app/staticfiles /app/media

EXPOSE 8000

ENV DJANGO_SETTINGS_MODULE=config.settings.prod

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]
