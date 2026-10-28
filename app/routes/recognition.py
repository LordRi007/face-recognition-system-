from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.user import User

recognition_bp = Blueprint("recognition", __name__, url_prefix="/face")


@recognition_bp.route("/enroll")
@login_required
def enroll():
    # If admin or staff, allow enrolling any user; regular users enroll themselves
    target_user_id = request.args.get("user_id", type=int)
    
    if current_user.is_staff and target_user_id:
        target_user = User.query.get_or_404(target_user_id)
    else:
        target_user = current_user

    # If already enrolled, provide notification
    return render_template("face/enrollment.html", target_user=target_user)


@recognition_bp.route("/verify")
@login_required
def verify():
    # Load users for 1-to-1 selection (if staff/admin kiosk, or current user)
    users = []
    if current_user.is_staff:
        users = User.query.filter_by(status="active").order_by(User.name.asc()).all()
    else:
        users = [current_user]

    preselected_id = request.args.get("user_id", default=current_user.id, type=int)

    return render_template(
        "face/verification.html",
        users=users,
        preselected_id=preselected_id,
        current_user=current_user
    )
