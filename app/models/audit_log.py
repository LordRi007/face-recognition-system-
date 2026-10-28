from datetime import datetime, timezone
from app.extensions import db


class AuditLog(db.Model):
    """Immutable audit trail for administrator and security-sensitive operations."""

    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    action = db.Column(db.String(50), nullable=False, index=True)
    target_type = db.Column(db.String(50), nullable=False, index=True)
    target_id = db.Column(db.String(50), nullable=True)
    details = db.Column(db.Text, nullable=True)
    
    ip_address = db.Column(db.String(45), nullable=True)
    timestamp = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    # Relationship to acting user
    actor = db.relationship("User", foreign_keys=[actor_id])

    @classmethod
    def log(cls, action: str, target_type: str, target_id=None, actor_id=None, details=None, ip_address=None):
        """Helper to create and persist an audit log entry."""
        entry = cls(
            actor_id=actor_id,
            action=action,
            target_type=target_type,
            target_id=str(target_id) if target_id is not None else None,
            details=details,
            ip_address=ip_address,
            timestamp=datetime.now(timezone.utc),
        )
        db.session.add(entry)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
        return entry

    def to_dict(self):
        return {
            "id": self.id,
            "actor_id": self.actor_id,
            "actor_name": self.actor.name if self.actor else "System / Anonymous",
            "action": self.action,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

    def __repr__(self):
        return f"<AuditLog action={self.action} actor={self.actor_id} time={self.timestamp}>"
