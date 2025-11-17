# M3 Timecode Validation Service - Dockerfile
# Multi-stage build for Cloud Run deployment

# Stage 1: Build stage with FFmpeg
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Production stage
FROM python:3.11-slim

# Install runtime dependencies (FFmpeg)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY app/ ./app/
COPY tests/ ./tests/

# Create directories for temporary files
RUN mkdir -p /tmp/frames /tmp/videos && \
    chown -R appuser:appuser /app /tmp/frames /tmp/videos

# Switch to non-root user
USER appuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV POKER_ENV=production
ENV PORT=8003
ENV FFMPEG_PATH=/usr/bin/ffmpeg

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8003/health')"

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8003", "--workers", "4", "--threads", "2", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "app.api:app"]
