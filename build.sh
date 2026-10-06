#!/usr/bin/env bash
# ==============================================================================
# Netra AI - Production Build Script for Cloud Platforms (Render, Railway, etc.)
# ==============================================================================
set -o errexit

echo "==> [1/4] Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "==> [2/4] Compiling English & Hindi translation catalogs..."
python scripts/compile_locales.py

echo "==> [3/4] Collecting static assets for WhiteNoise..."
python manage.py collectstatic --noinput

echo "==> [4/5] Applying database schema migrations..."
python manage.py migrate

echo "==> [5/5] Ensuring default admin and demo user accounts exist..."
python manage.py ensure_admin

echo "==> Build completed successfully! Ready for Daphne ASGI."

