# Face Recognition Management System (FRMS) - Production Dockerfile
FROM python:3.12-slim-bookworm

# System dependencies for OpenCV, GUI bindings, and C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set environment flags
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PORT=5000

WORKDIR /app

# Create unprivileged user for container security
RUN groupadd -r frms && useradd -r -g frms -d /app -s /sbin/nologin frms

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Ensure storage directories exist with correct permissions
RUN mkdir -p /app/uploads /app/temp_uploads /app/instance && \
    chown -R frms:frms /app

USER frms

EXPOSE 5000
EXPOSE 7860

# Health check (dynamic port)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-5000}/ || exit 1

CMD ["gunicorn", "-c", "gunicorn.conf.py", "run:app"]
