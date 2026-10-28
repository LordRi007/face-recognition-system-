from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.audit_log import AuditLog
from app.models.attendance import VerificationLog

logs_bp = Blueprint("logs", __name__, url_prefix="/logs")


@logs_bp.route("/audit")
@login_required
def audit_logs():
    if not current_user.is_admin:
        flash("Access restricted to administrators.", "danger")
        return redirect(url_for("dashboard.index"))

    action_filter = request.args.get("action")
    query = AuditLog.query

    if action_filter:
        query = query.filter(AuditLog.action == action_filter)

    logs = query.order_by(AuditLog.timestamp.desc()).limit(100).all()

    # Get distinct action types for filter dropdown
    distinct_actions = [
        r[0] for r in AuditLog.query.with_entities(AuditLog.action).distinct().all()
    ]

    return render_template(
        "logs/audit.html",
        logs=logs,
        distinct_actions=distinct_actions,
        selected_action=action_filter
    )


@logs_bp.route("/verification")
@login_required
def verification_logs():
    if not current_user.is_staff:
        flash("Access restricted to staff and administrators.", "warning")
        return redirect(url_for("dashboard.index"))

    result_filter = request.args.get("result")
    query = VerificationLog.query

    if result_filter:
        query = query.filter(VerificationLog.result == result_filter)

    logs = query.order_by(VerificationLog.timestamp.desc()).limit(100).all()

    return render_template(
        "logs/verification.html",
        logs=logs,
        selected_result=result_filter
    )
