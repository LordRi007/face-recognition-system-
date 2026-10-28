from datetime import datetime, timezone, date, timedelta
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.services.report_service import ReportService
from app.models.department import Department
from app.models.attendance import Attendance

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@reports_bp.route("")
@login_required
def index():
    if not current_user.is_staff:
        flash("Access denied. Reports are restricted to staff and administrators.", "warning")
        return redirect(url_for("dashboard.index"))

    metrics = ReportService.get_dashboard_metrics()
    trends = ReportService.get_attendance_trends(days=14)
    breakdown = ReportService.get_verification_breakdown()
    dept_stats = ReportService.get_department_stats()

    return render_template(
        "reports/index.html",
        metrics=metrics,
        trends=trends,
        breakdown=breakdown,
        dept_stats=dept_stats
    )
