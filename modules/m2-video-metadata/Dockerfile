# M2 Video Metadata Service - Production Dockerfile

FROM python:3.11-slim

# Install FFmpeg and system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Set environment variables
ENV PORT=8002
ENV PYTHONUNBUFFERED=1
ENV GCP_PROJECT_ID=gg-poker
ENV BIGQUERY_DATASET=prod
ENV BIGQUERY_TABLE=video_files
ENV GCS_BUCKET=gg-poker-proxy
ENV LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Run with gunicorn
# 2 workers, 4 threads per worker, 10 minute timeout for long operations
CMD exec gunicorn \
    --bind :${PORT} \
    --workers 2 \
    --threads 4 \
    --timeout 600 \
    --access-logfile - \
    --error-logfile - \
    --log-level ${LOG_LEVEL} \
    app.api:app
