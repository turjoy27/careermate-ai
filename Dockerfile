# Multi-stage production Dockerfile for CareerMate AI
FROM python:3.14-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install system dependencies (build-essential, pkg-config, default-libmysqlclient-dev for MySQL/Pillow)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    libjpeg-dev \
    zlib1g-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . /app/

# Collect static files
RUN cd backend && python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "careermate_core.wsgi:application", "--chdir", "backend", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
