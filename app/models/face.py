from datetime import datetime, timezone
from app.extensions import db


class FaceEnrollment(db.Model):
    """Stores encrypted facial embeddings and consent metadata for a user."""

    __tablename__ = "face_enrollments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    # Encrypted biometric vector (Fernet AES ciphertext storing serialized float array)
    encrypted_embedding = db.Column(db.Text, nullable=False)
    
    # Model tracking metadata
    model_name = db.Column(db.String(50), default="Facenet512", nullable=False)
    model_version = db.Column(db.String(20), default="1.0", nullable=False)
    embedding_dimension = db.Column(db.Integer, default=512, nullable=False)
    samples_count = db.Column(db.Integer, default=1, nullable=False)
    quality_score = db.Column(db.Float, nullable=True)

    # Consent tracking
    consent_timestamp = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    consent_version = db.Column(db.String(20), default="1.0", nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Timestamps
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    user = db.relationship("User", back_populates="face_enrollment")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "embedding_dimension": self.embedding_dimension,
            "samples_count": self.samples_count,
            "quality_score": round(self.quality_score, 2) if self.quality_score else None,
            "consent_timestamp": self.consent_timestamp.isoformat() if self.consent_timestamp else None,
            "consent_version": self.consent_version,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<FaceEnrollment user_id={self.user_id} model={self.model_name}>"
