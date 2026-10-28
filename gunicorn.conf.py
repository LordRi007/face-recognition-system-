import multiprocessing
import os

# Server socket binding
port = os.getenv("PORT", "5000")
bind = os.getenv("GUNICORN_BIND", f"0.0.0.0:{port}")
backlog = 2048

# Worker Processes
# For AI/DeepFace inference on VPS, 2-3 workers prevent RAM exhaustion
workers = int(os.getenv("GUNICORN_WORKERS", 2))
worker_class = "sync"
threads = int(os.getenv("GUNICORN_THREADS", 2))
worker_connections = 1000

# Timeout: Face recognition inference on CPU can take a few seconds
timeout = int(os.getenv("GUNICORN_TIMEOUT", 120))
keepalive = 5

# Process naming
proc_name = "frms_gunicorn"

# Logging
accesslog = os.getenv("GUNICORN_ACCESS_LOG", "-")
errorlog = os.getenv("GUNICORN_ERROR_LOG", "-")
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")

# Lifecycle Hooks
def on_starting(server):
    server.log.info("Starting Face Recognition Management System (FRMS) Gunicorn master...")

def worker_int(worker):
    worker.log.info(f"Worker {worker.pid} interrupted, shutting down gracefully...")
