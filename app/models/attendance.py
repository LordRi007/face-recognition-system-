from datetime import datetime, timezone, date
from app.extensions import db


class Attendance(db.Model):
    """Attendance log for check-in / check-out."""

    __tablename__ = "attendances"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date = db.Column(db.Date, default=lambda: datetime.now(timezone.utc).date(), nullable=False, index=True)
    
    check_in = db.Column(db.DateTime, nullable=True)
    check_out = db.Column(db.DateTime, nullable=True)
    
    # 'facial', 'manual_pin', 'admin_override'
    verification_method = db.Column(db.String(30), default="facial", nullable=False)
    # 'present', 'late', 'half_day', 'absent'
    status = db.Column(db.String(20), default="present", nullable=False, index=True)
    
    notes = db.Column(db.String(255), nullable=True)
    updated_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

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
    user = db.relationship("User", foreign_keys=[user_id], back_populates="attendances")
    updated_by = db.relationship("User", foreign_keys=[updated_by_id])

    # Unique constraint per user per date
    __table_args__ = (
        db.UniqueConstraint("user_id", "date", name="uq_user_attendance_date"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else None,
            "department": self.user.department.name if self.user and self.user.department else None,
            "date": self.date.isoformat() if self.date else None,
            "check_in": self.check_in.strftime("%H:%M:%S") if self.check_in else None,
            "check_out": self.check_out.strftime("%H:%M:%S") if self.check_out else None,
            "verification_method": self.verification_method,
            "status": self.status,
            "notes": self.notes,
            "updated_by": self.updated_by.name if self.updated_by else None,
        }

    def __repr__(self):
        return f"<Attendance user_id={self.user_id} date={self.date} status={self.status}>"


class VerificationLog(db.Model):
    """
    Log of facial and alternative identity verification attempts.
    NOTE: Biometric images or raw embeddings are strictly NEVER stored here.
    """

    __tablename__ = "verification_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # 'success', 'failure', 'no_face', 'multiple_faces', 'poor_quality', 'spoof_detected'
    result = db.Column(db.String(30), nullable=False, index=True)
    # 'webcam', 'upload', 'alternative_pin'
    verification_method = db.Column(db.String(30), default="webcam", nullable=False)
    
    # Mathematical comparison metrics (no biometric data)
    distance_score = db.Column(db.Float, nullable=True)
    threshold_used = db.Column(db.Float, nullable=True)
    error_code = db.Column(db.String(50), nullable=True)
    
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    # Relationships
    user = db.relationship("User", back_populates="verification_logs")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else "Anonymous / Unknown",
            "result": self.result,
            "verification_method": self.verification_method,
            "distance_score": round(self.distance_score, 4) if self.distance_score is not None else None,
            "threshold_used": self.threshold_used,
            "error_code": self.error_code,
            "ip_address": self.ip_address,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

    def __repr__(self):
        return f"<VerificationLog user_id={self.user_id} result={self.result} time={self.timestamp}>"
