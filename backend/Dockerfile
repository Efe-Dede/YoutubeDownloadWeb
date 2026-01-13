# Backend Dockerfile - Production Ready
FROM python:3.11-slim

# Install FFmpeg and cleanup in same layer to reduce size
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create downloads directory with proper permissions
RUN mkdir -p /app/downloads && chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Environment variables
ENV PORT=8000
ENV HOST=0.0.0.0
ENV DOWNLOAD_DIR=/app/downloads
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose port (internal only, Coolify handles external routing)
EXPOSE ${PORT}

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health')" || exit 1

# Run the application
CMD ["sh", "-c", "uvicorn app.main:app --host ${HOST} --port ${PORT}"]
