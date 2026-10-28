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

# Create user with UID 1000 for Hugging Face Spaces compatibility
RUN useradd -m -u 1000 frms

# Set environment flags
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PORT=7860 \
    HOME=/home/frms

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Ensure storage directories exist with correct permissions
RUN mkdir -p /app/uploads /app/temp_uploads /app/instance && \
    chown -R frms:frms /app /home/frms

USER frms

EXPOSE 7860
EXPOSE 5000

# Health check (dynamic port)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-7860}/login || exit 1

CMD ["gunicorn", "-c", "gunicorn.conf.py", "run:app"]
