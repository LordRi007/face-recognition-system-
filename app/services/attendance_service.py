from datetime import datetime, timezone, date, time
from typing import Optional, Dict, Any, List
from flask import current_app
from app.extensions import db
from app.models.attendance import Attendance
from app.models.user import User
from app.services.security_service import SecurityService


class AttendanceService:
    """Service handling attendance check-in, check-out, late calculations, and corrections."""

    @staticmethod
    def get_late_threshold_time() -> time:
        """Parses configured late threshold (default 09:15:00)."""
        time_str = current_app.config.get("ATTENDANCE_LATE_THRESHOLD_TIME", "09:15:00") if current_app else "09:15:00"
        try:
            parts = [int(p) for p in time_str.split(":")]
            return time(hour=parts[0], minute=parts[1], second=parts[2] if len(parts) > 2 else 0)
        except Exception:
            return time(hour=9, minute=15, second=0)

    @classmethod
    def process_check_in(
        cls,
        user_id: int,
        verification_method: str = "facial",
        custom_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Records a check-in event for the user today.
        Computes late status if checked in past the configured threshold.
        """
        today = datetime.now(timezone.utc).date()
        now_dt = datetime.now(timezone.utc)
        current_local_time = now_dt.time()

        user = User.query.get(user_id)
        if not user:
            return {"success": False, "message": "User not found."}

        record = Attendance.query.filter_by(user_id=user_id, date=today).first()
        if record and record.check_in:
            return {
                "success": False,
                "message": f"User {user.name} already checked in today at {record.check_in.strftime('%H:%M:%S')} UTC.",
                "record": record.to_dict(),
            }

        # Determine late status
        threshold = cls.get_late_threshold_time()
        is_late = current_local_time > threshold
        status = "late" if is_late else "present"
        
        notes = custom_notes
        if is_late and not notes:
            minutes_late = (
                (current_local_time.hour * 60 + current_local_time.minute) -
                (threshold.hour * 60 + threshold.minute)
            )
            notes = f"Arrived {minutes_late} min after standard cutoff ({threshold.strftime('%H:%M')})."

        if record:
            record.check_in = now_dt
            record.verification_method = verification_method
            record.status = status
            if notes:
                record.notes = notes
        else:
            record = Attendance(
                user_id=user_id,
                date=today,
                check_in=now_dt,
                verification_method=verification_method,
                status=status,
                notes=notes
            )
            db.session.add(record)

        db.session.commit()

        SecurityService.log_event(
            action="ATTENDANCE_CHECK_IN",
            target_type="Attendance",
            target_id=record.id,
            actor_id=user_id,
            details=f"Check-in verified via {verification_method}. Status: {status}."
        )

        return {
            "success": True,
            "message": f"Check-in successful! Welcome, {user.name} ({status.capitalize()}).",
            "status": status,
            "record": record.to_dict(),
        }

    @classmethod
    def process_check_out(
        cls,
        user_id: int,
        verification_method: str = "facial",
        custom_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Records a check-out event for the user today."""
        today = datetime.now(timezone.utc).date()
        now_dt = datetime.now(timezone.utc)

        user = User.query.get(user_id)
        if not user:
            return {"success": False, "message": "User not found."}

        record = Attendance.query.filter_by(user_id=user_id, date=today).first()
        if not record:
            # Check-out with no check-in recorded
            record = Attendance(
                user_id=user_id,
                date=today,
                check_out=now_dt,
                verification_method=verification_method,
                status="present",
                notes=custom_notes or "Checked out without recorded morning check-in."
            )
            db.session.add(record)
        else:
            if record.check_out:
                return {
                    "success": False,
                    "message": f"User {user.name} already checked out today at {record.check_out.strftime('%H:%M:%S')} UTC.",
                    "record": record.to_dict(),
                }
            record.check_out = now_dt
            if custom_notes:
                record.notes = (record.notes + " | " + custom_notes) if record.notes else custom_notes

        db.session.commit()

        SecurityService.log_event(
            action="ATTENDANCE_CHECK_OUT",
            target_type="Attendance",
            target_id=record.id,
            actor_id=user_id,
            details=f"Check-out verified via {verification_method}."
        )

        return {
            "success": True,
            "message": f"Check-out successful! Goodbye, {user.name}.",
            "record": record.to_dict(),
        }

    @classmethod
    def admin_correct_attendance(
        cls,
        attendance_id: int,
        admin_id: int,
        new_status: str,
        new_check_in: Optional[datetime],
        new_check_out: Optional[datetime],
        reason: str
    ) -> Dict[str, Any]:
        """Allows authorized administrators to manually adjust attendance with audit logging."""
        record = Attendance.query.get(attendance_id)
        if not record:
            return {"success": False, "message": "Attendance record not found."}

        old_state = f"status={record.status}, in={record.check_in}, out={record.check_out}"

        record.status = new_status
        record.check_in = new_check_in
        record.check_out = new_check_out
        record.updated_by_id = admin_id
        record.notes = f"Admin correction: {reason}"
        record.verification_method = "admin_override"

        db.session.commit()

        SecurityService.log_event(
            action="ATTENDANCE_CORRECTION",
            target_type="Attendance",
            target_id=record.id,
            actor_id=admin_id,
            details=f"Correction applied. Old state: [{old_state}]. Reason: {reason}"
        )

        return {"success": True, "message": "Attendance record updated successfully.", "record": record.to_dict()}
