from datetime import datetime, timezone, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager


class User(UserMixin, db.Model):
    """User model representing staff, administrators, and regular users."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(30), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Organization & Access Control
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True, index=True)
    role = db.Column(db.String(20), default="user", nullable=False, index=True)  # 'admin', 'staff', 'user'
    status = db.Column(db.String(20), default="active", nullable=False, index=True)  # 'active', 'inactive', 'suspended'
    profile_image = db.Column(db.String(255), nullable=True)

    # Security: Rate limiting & account lockout
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime, nullable=True)
    last_login_at = db.Column(db.DateTime, nullable=True)

    # Alternative verification PIN (hashed, optional fallback if biometric fails)
    pin_hash = db.Column(db.String(255), nullable=True)

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
    department = db.relationship("Department", back_populates="users")
    face_enrollment = db.relationship(
        "FaceEnrollment",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    attendances = db.relationship(
        "Attendance",
        foreign_keys="[Attendance.user_id]",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="desc(Attendance.date)"
    )
    verification_logs = db.relationship(
        "VerificationLog",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="desc(VerificationLog.timestamp)"
    )

    # Password management
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    # PIN management for alternative verification
    def set_pin(self, pin: str) -> None:
        if pin:
            self.pin_hash = generate_password_hash(str(pin), method="pbkdf2:sha256")
        else:
            self.pin_hash = None

    def check_pin(self, pin: str) -> bool:
        if not self.pin_hash or not pin:
            return False
        return check_password_hash(self.pin_hash, str(pin))

    # Account Lockout logic
    def is_locked(self) -> bool:
        if self.locked_until is None:
            return False
        now = datetime.now(timezone.utc)
        # Handle naive or aware datetimes
        locked_time = self.locked_until
        if locked_time.tzinfo is None:
            locked_time = locked_time.replace(tzinfo=timezone.utc)
        if now < locked_time:
            return True
        # Lockout expired, reset
        self.locked_until = None
        self.failed_login_attempts = 0
        db.session.commit()
        return False

    def record_failed_login(self, max_attempts: int = 5, lockout_minutes: int = 15) -> None:
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= max_attempts:
            self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=lockout_minutes)
        db.session.commit()

    def reset_failed_logins(self) -> None:
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login_at = datetime.now(timezone.utc)
        db.session.commit()

    # Role helpers
    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_staff(self) -> bool:
        return self.role in ("admin", "staff")

    @property
    def is_active_account(self) -> bool:
        return self.status == "active"

    # Flask-Login override
    @property
    def is_active(self) -> bool:
        return self.status == "active" and not self.is_locked()

    @property
    def has_face_enrolled(self) -> bool:
        return self.face_enrollment is not None and self.face_enrollment.is_active

    def to_dict(self, include_sensitive: bool = False):
        data = {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "department_id": self.department_id,
            "department_name": self.department.name if self.department else None,
            "role": self.role,
            "status": self.status,
            "profile_image": self.profile_image,
            "has_face_enrolled": self.has_face_enrolled,
            "has_pin": bool(self.pin_hash),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }
        if include_sensitive:
            data.update({
                "failed_login_attempts": self.failed_login_attempts,
                "is_locked": self.is_locked(),
                "locked_until": self.locked_until.isoformat() if self.locked_until else None,
            })
        return data

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
