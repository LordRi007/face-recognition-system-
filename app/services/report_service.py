import csv
import io
from datetime import datetime, timezone, date, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import func
from app.extensions import db
from app.models.user import User
from app.models.department import Department
from app.models.attendance import Attendance, VerificationLog
from app.models.face import FaceEnrollment


class ReportService:
    """Provides statistical aggregations, analytics, and data export for FRMS."""

    @classmethod
    def get_dashboard_metrics(cls) -> Dict[str, Any]:
        """Calculates headline numbers for the executive/admin dashboard."""
        today = datetime.now(timezone.utc).date()

        total_users = User.query.filter(User.status != "suspended").count()
        enrolled_faces = FaceEnrollment.query.filter_by(is_active=True).count()
        
        # Today's attendance
        today_attendance = Attendance.query.filter_by(date=today).all()
        today_present_count = len([a for a in today_attendance if a.status in ("present", "late")])
        today_late_count = len([a for a in today_attendance if a.status == "late"])
        today_absent_count = max(0, total_users - today_present_count)
        
        # All-time verification logs
        total_verifications = VerificationLog.query.count()
        successful_verifications = VerificationLog.query.filter_by(result="success").count()
        failed_verifications = total_verifications - successful_verifications
        success_rate = round((successful_verifications / total_verifications * 100), 1) if total_verifications > 0 else 100.0

        # System health status
        health = {
            "database": "online",
            "biometric_engine": "ready",
            "encryption": "active",
        }

        return {
            "total_users": total_users,
            "enrolled_faces": enrolled_faces,
            "today_present": today_present_count,
            "today_late": today_late_count,
            "today_absent": today_absent_count,
            "total_verifications": total_verifications,
            "successful_verifications": successful_verifications,
            "failed_verifications": failed_verifications,
            "verification_success_rate": success_rate,
            "health": health,
        }

    @classmethod
    def get_attendance_trends(cls, days: int = 7) -> Dict[str, Any]:
        """Calculates daily attendance counts for the past N days for Chart.js."""
        today = datetime.now(timezone.utc).date()
        date_labels = []
        present_counts = []
        late_counts = []

        for i in range(days - 1, -1, -1):
            d = today - timedelta(days=i)
            date_labels.append(d.strftime("%b %d"))
            
            day_records = Attendance.query.filter_by(date=d).all()
            p = len([r for r in day_records if r.status == "present"])
            l = len([r for r in day_records if r.status == "late"])
            present_counts.append(p)
            late_counts.append(l)

        return {
            "labels": date_labels,
            "present": present_counts,
            "late": late_counts,
        }

    @classmethod
    def get_verification_breakdown(cls) -> Dict[str, Any]:
        """Computes verification results breakdown for Chart.js doughnut chart."""
        results = db.session.query(
            VerificationLog.result, func.count(VerificationLog.id)
        ).group_by(VerificationLog.result).all()

        labels = []
        counts = []
        mapping = {
            "success": "Verified (Match)",
            "failure": "Biometric Mismatch",
            "no_face": "No Face Detected",
            "multiple_faces": "Multiple Faces",
            "poor_quality": "Poor Image Quality",
            "spoof_detected": "Spoof / Presentation Attack",
        }

        for res, count in results:
            labels.append(mapping.get(res, res.replace("_", " ").title()))
            counts.append(count)

        if not labels:
            labels = ["Verified (Match)", "Biometric Mismatch"]
            counts = [0, 0]

        return {"labels": labels, "counts": counts}

    @classmethod
    def get_department_stats(cls) -> List[Dict[str, Any]]:
        """Aggregates user enrollment and today's attendance by department."""
        today = datetime.now(timezone.utc).date()
        departments = Department.query.all()
        stats = []

        for dept in departments:
            dept_users = User.query.filter_by(department_id=dept.id, status="active").all()
            user_count = len(dept_users)
            user_ids = [u.id for u in dept_users]
            
            enrolled_count = FaceEnrollment.query.filter(
                FaceEnrollment.user_id.in_(user_ids),
                FaceEnrollment.is_active == True
            ).count() if user_ids else 0

            present_today = Attendance.query.filter(
                Attendance.user_id.in_(user_ids),
                Attendance.date == today,
                Attendance.status.in_(["present", "late"])
            ).count() if user_ids else 0

            attendance_pct = round((present_today / user_count * 100), 1) if user_count > 0 else 0.0

            stats.append({
                "id": dept.id,
                "name": dept.name,
                "user_count": user_count,
                "enrolled_count": enrolled_count,
                "present_today": present_today,
                "attendance_rate": attendance_pct,
            })

        return stats

    @classmethod
    def export_attendance_csv(
        cls,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        department_id: Optional[int] = None
    ) -> str:
        """
        Exports filtered attendance records to CSV string.
        Uses standard Python csv module for zero external dependency overhead.
        """
        query = Attendance.query.join(User, Attendance.user_id == User.id)

        if start_date:
            query = query.filter(Attendance.date >= start_date)
        if end_date:
            query = query.filter(Attendance.date <= end_date)
        if department_id:
            query = query.filter(User.department_id == department_id)

        records = query.order_by(Attendance.date.desc(), User.name.asc()).all()

        output = io.StringIO()
        writer = csv.writer(output)

        # Header row
        writer.writerow([
            "Attendance ID",
            "Date",
            "User ID",
            "Full Name",
            "Email",
            "Department",
            "Check-In (UTC)",
            "Check-Out (UTC)",
            "Verification Method",
            "Status",
            "Notes",
            "Updated By"
        ])

        for r in records:
            writer.writerow([
                r.id,
                r.date.isoformat() if r.date else "",
                r.user.id if r.user else "",
                r.user.name if r.user else "Unknown",
                r.user.email if r.user else "",
                r.user.department.name if r.user and r.user.department else "None",
                r.check_in.strftime("%H:%M:%S") if r.check_in else "",
                r.check_out.strftime("%H:%M:%S") if r.check_out else "",
                r.verification_method,
                r.status.capitalize(),
                r.notes or "",
                r.updated_by.name if r.updated_by else ""
            ])

        return output.getvalue()
