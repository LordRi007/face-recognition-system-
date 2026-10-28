from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.services.report_service import ReportService
from app.services.security_service import SecurityService
from app.models.attendance import Attendance, VerificationLog
from app.models.department import Department
from app.models.user import User

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
@login_required
def index():
    metrics = ReportService.get_dashboard_metrics()
    trends = ReportService.get_attendance_trends(days=7)
    breakdown = ReportService.get_verification_breakdown()
    recent_verifications = VerificationLog.query.order_by(VerificationLog.timestamp.desc()).limit(8).all()
    
    return render_template(
        "dashboard.html",
        metrics=metrics,
        trends=trends,
        breakdown=breakdown,
        recent_verifications=recent_verifications
    )


@dashboard_bp.route("/privacy")
def privacy():
    return render_template("privacy.html")


@dashboard_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if not current_user.is_admin:
        flash("Access denied. Only administrators may modify system settings.", "danger")
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        threshold = request.form.get("face_match_threshold")
        min_blur = request.form.get("quality_min_blur_score")
        min_bright = request.form.get("quality_min_brightness")
        max_bright = request.form.get("quality_max_brightness")
        late_cutoff = request.form.get("attendance_late_threshold_time")

        if threshold:
            current_app.config["FACE_MATCH_THRESHOLD"] = float(threshold)
        if min_blur:
            current_app.config["QUALITY_MIN_BLUR_SCORE"] = float(min_blur)
        if min_bright:
            current_app.config["QUALITY_MIN_BRIGHTNESS"] = float(min_bright)
        if max_bright:
            current_app.config["QUALITY_MAX_BRIGHTNESS"] = float(max_bright)
        if late_cutoff:
            current_app.config["ATTENDANCE_LATE_THRESHOLD_TIME"] = late_cutoff

        SecurityService.log_event(
            action="SETTINGS_UPDATED",
            target_type="SystemConfig",
            actor_id=current_user.id,
            details=f"Updated thresholds: Match={threshold}, Blur={min_blur}, Brightness={min_bright}-{max_bright}, LateCutoff={late_cutoff}"
        )
        flash("System configuration parameters updated successfully.", "success")
        return redirect(url_for("dashboard.settings"))

    return render_template("settings.html")
