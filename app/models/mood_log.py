from datetime import datetime, timezone
import json
from app.extensions import db


class MoodLog(db.Model):
    """
    Stores historical camera face mood and feeling check-ins.
    Tracks emotional valence, arousal, dominant feeling, and breakdown scores.
    """
    __tablename__ = "mood_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    dominant_mood = db.Column(db.String(32), nullable=False, index=True)
    feeling_tag = db.Column(db.String(64), nullable=True)
    emoji = db.Column(db.String(8), nullable=True, default="😊")
    confidence = db.Column(db.Float, nullable=False, default=85.0)
    valence = db.Column(db.Float, nullable=False, default=0.0)      # -1.0 (unpleasant) to +1.0 (pleasant)
    arousal = db.Column(db.Float, nullable=False, default=0.5)      # 0.0 (calm/sleepy) to 1.0 (energetic/excited)
    breakdown_json = db.Column(db.Text, nullable=True)
    context = db.Column(db.String(64), nullable=False, default="camera_tracker")  # camera_tracker, attendance, wellness_check
    note = db.Column(db.String(255), nullable=True)
    captured_image = db.Column(db.Text, nullable=True)  # Base64 JPEG data URL of face snapshot
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    user = db.relationship("User", backref=db.backref("mood_logs", lazy="dynamic", cascade="all, delete-orphan"))

    def get_breakdown(self):
        if not self.breakdown_json:
            return {}
        try:
            return json.loads(self.breakdown_json)
        except Exception:
            return {}

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else "Anonymous Guest",
            "dominant_mood": self.dominant_mood,
            "feeling_tag": self.feeling_tag,
            "emoji": self.emoji,
            "confidence": round(self.confidence, 1),
            "valence": round(self.valence, 2),
            "arousal": round(self.arousal, 2),
            "breakdown": self.get_breakdown(),
            "context": self.context,
            "note": self.note,
            "captured_image": self.captured_image,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "time_formatted": self.timestamp.strftime("%b %d, %Y %I:%M %p") if self.timestamp else ""
        }
