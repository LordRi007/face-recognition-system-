import pytest
from datetime import datetime, timezone, date
from app.services.attendance_service import AttendanceService
from app.models.attendance import Attendance
from app.models.audit_log import AuditLog
from app.extensions import db


def test_attendance_check_in_and_duplicate_prevention(app, seed_data):
    """Verify check-in creates record and subsequent check-in reports already checked in."""
    with app.app_context():
        user = seed_data["user"]
        
        # 1. First check-in
        result1 = AttendanceService.process_check_in(user_id=user.id, verification_method="facial")
        assert result1["success"] is True
        assert result1["status"] in ("present", "late")

        today_rec = Attendance.query.filter_by(user_id=user.id, date=datetime.now(timezone.utc).date()).first()
        assert today_rec is not None
        assert today_rec.check_in is not None

        # 2. Second duplicate check-in today
        result2 = AttendanceService.process_check_in(user_id=user.id, verification_method="facial")
        assert result2["success"] is False
        assert "already checked in" in result2["message"].lower()


def test_attendance_check_out(app, seed_data):
    """Verify check-out updates today's record."""
    with app.app_context():
        user = seed_data["user"]
        # Check in first
        AttendanceService.process_check_in(user_id=user.id, verification_method="facial")
        
        # Now check out
        out_res = AttendanceService.process_check_out(user_id=user.id, verification_method="facial")
        assert out_res["success"] is True

        today_rec = Attendance.query.filter_by(user_id=user.id, date=datetime.now(timezone.utc).date()).first()
        assert today_rec.check_out is not None


def test_admin_attendance_correction(app, seed_data):
    """Verify administrator manual correction updates record and logs audit trail."""
    with app.app_context():
        admin = seed_data["admin"]
        user = seed_data["user"]

        # User checks in
        att_res = AttendanceService.process_check_in(user_id=user.id)
        att_id = att_res["record"]["id"]

        # Admin corrects record to 'present' with custom check-in time
        corr_res = AttendanceService.admin_correct_attendance(
            attendance_id=att_id,
            admin_id=admin.id,
            new_status="present",
            new_check_in=datetime.now(timezone.utc),
            new_check_out=None,
            reason="Card reader glitch verified by front desk"
        )
        assert corr_res["success"] is True

        # Check audit log was created
        audit_entry = AuditLog.query.filter_by(
            action="ATTENDANCE_CORRECTION",
            target_id=str(att_id)
        ).first()
        assert audit_entry is not None
        assert "Card reader glitch" in audit_entry.details
