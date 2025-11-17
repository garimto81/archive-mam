# M5 Clipping Service - Flask API Server
# Multi-stage build for optimized image size

FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY local_agent/ ./local_agent/

# Create non-root user
RUN useradd -m -u 1000 poker && \
    chown -R poker:poker /app

USER poker

# Expose port
EXPOSE 8005

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV POKER_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8005/health').raise_for_status()"

# Run API server with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8005", "--workers", "4", "--timeout", "120", "app.api:app"]
