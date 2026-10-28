import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Prevent OpenBLAS thread allocation exhaustion on Windows
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class Config:
    """Base application configuration."""

    # Secret & Session security
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-fallback-secret-key-change-me")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False").lower() in ("true", "1", "yes")
    PERMANENT_SESSION_LIFETIME = timedelta(
        seconds=int(os.getenv("PERMANENT_SESSION_LIFETIME", 3600))
    )

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'face_recognition.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }

    # Uploads & File Handling
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    TEMP_UPLOAD_FOLDER = os.path.join(BASE_DIR, "temp_uploads")

    # Biometric Encryption (Fernet 32-byte key)
    BIOMETRIC_ENCRYPTION_KEY = os.getenv(
        "BIOMETRIC_ENCRYPTION_KEY",
        "W3dYvGqgV4u2N_VjS4w1n-X98oQ5P6a0M8b4Z2l1Y6A="
    )

    # Face Recognition AI Parameters
    FACENET_MODEL_NAME = os.getenv("FACENET_MODEL_NAME", "ArcFace")
    FACE_DETECTOR_BACKEND = os.getenv("FACE_DETECTOR_BACKEND", "ultraface_onnx")
    FACE_DISTANCE_METRIC = os.getenv("FACE_DISTANCE_METRIC", "cosine")
    # Distance threshold: ArcFace cosine distance <= 0.50 indicates a match
    FACE_MATCH_THRESHOLD = float(os.getenv("FACE_MATCH_THRESHOLD", 0.50))
    SAME_PERSON_THRESHOLD = float(os.getenv("SAME_PERSON_THRESHOLD", 0.48))

    # Image Quality Thresholds
    QUALITY_MIN_BLUR_SCORE = float(os.getenv("QUALITY_MIN_BLUR_SCORE", 25.0))
    QUALITY_MIN_BRIGHTNESS = float(os.getenv("QUALITY_MIN_BRIGHTNESS", 30.0))
    QUALITY_MAX_BRIGHTNESS = float(os.getenv("QUALITY_MAX_BRIGHTNESS", 235.0))

    # Security & Rate Limiting
    RATE_LIMIT_LOGIN_ATTEMPTS = int(os.getenv("RATE_LIMIT_LOGIN_ATTEMPTS", 5))
    RATE_LIMIT_LOCKOUT_MINUTES = int(os.getenv("RATE_LIMIT_LOCKOUT_MINUTES", 15))

    # Attendance defaults
    ATTENDANCE_LATE_THRESHOLD_TIME = os.getenv("ATTENDANCE_LATE_THRESHOLD_TIME", "09:15:00")


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    QUALITY_MIN_BLUR_SCORE = 10.0  # More lenient for mock test fixtures
    SAME_PERSON_THRESHOLD = 0.25  # In synthetic tests, drawn geometric ellipses have ~0.257 distance


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    # Ensure DATABASE_URL is set in production
    if os.getenv("DATABASE_URL") and os.getenv("DATABASE_URL").startswith("postgres://"):
        # Fix Heroku/old-style postgres:// to postgresql://
        SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL").replace("postgres://", "postgresql://", 1)


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
