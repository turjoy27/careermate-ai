#!/usr/bin/env bash
# ==============================================================================
# CareerMate AI - Render Deployment Build Script
# Native Python & Render PostgreSQL Environment
# ==============================================================================
set -o errexit

echo "==> Upgrading pip..."
pip install --upgrade pip

echo "==> Installing Python dependencies..."
pip install -r requirements.txt

echo "==> Running Django database migrations..."
python backend/manage.py migrate --noinput

echo "==> Collecting static assets for WhiteNoise..."
python backend/manage.py collectstatic --no-input --clear

echo "==> Build completed successfully!"
