from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models.user import User
from app.services.security_service import SecurityService

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        if not email or not password:
            flash("Please enter both email address and password.", "danger")
            return render_template("auth/login.html")

        user = User.query.filter_by(email=email).first()

        # Check if user exists
        if not user:
            flash("Invalid email or password.", "danger")
            SecurityService.log_event(
                action="LOGIN_FAILED",
                target_type="User",
                details=f"Login attempt failed for non-existent email: {email}"
            )
            return render_template("auth/login.html")

        # Check account lockout
        if user.is_locked():
            lockout_time = user.locked_until.strftime("%H:%M:%S") if user.locked_until else "a few minutes"
            flash(f"Account is temporarily locked due to excessive failed attempts. Try again after {lockout_time} UTC.", "danger")
            SecurityService.log_event(
                action="LOGIN_LOCKED",
                target_type="User",
                target_id=user.id,
                details=f"Locked account attempted login: {email}"
            )
            return render_template("auth/login.html")

        # Check account active status
        if user.status != "active":
            flash("Your account has been deactivated or suspended. Please contact an administrator.", "warning")
            return render_template("auth/login.html")

        # Verify password
        if not user.check_password(password):
            max_attempts = current_app.config.get("RATE_LIMIT_LOGIN_ATTEMPTS", 5)
            lockout_minutes = current_app.config.get("RATE_LIMIT_LOCKOUT_MINUTES", 15)
            user.record_failed_login(max_attempts=max_attempts, lockout_minutes=lockout_minutes)
            
            remaining = max(0, max_attempts - user.failed_login_attempts)
            if remaining == 0:
                flash(f"Account locked for {lockout_minutes} minutes due to {max_attempts} failed attempts.", "danger")
            else:
                flash(f"Invalid email or password. {remaining} attempt(s) remaining before lockout.", "danger")

            SecurityService.log_event(
                action="LOGIN_FAILED",
                target_type="User",
                target_id=user.id,
                actor_id=user.id,
                details=f"Failed password attempt. Consecutive fails: {user.failed_login_attempts}"
            )
            return render_template("auth/login.html")

        # Password valid: reset failed attempts and log in
        user.reset_failed_logins()
        login_user(user, remember=remember)

        SecurityService.log_event(
            action="LOGIN_SUCCESS",
            target_type="User",
            target_id=user.id,
            actor_id=user.id,
            details=f"User logged in successfully with role '{user.role}'."
        )

        flash(f"Welcome back, {user.name}!", "success")
        next_page = request.args.get("next")
        # Validate next_page to prevent open redirect
        if not next_page or not next_page.startswith("/"):
            next_page = url_for("dashboard.index")
        return redirect(next_page)

    return render_template("auth/login.html")


@auth_bp.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    user_id = current_user.id
    user_name = current_user.name
    logout_user()
    SecurityService.log_event(
        action="LOGOUT",
        target_type="User",
        target_id=user_id,
        actor_id=user_id,
        details=f"User {user_name} logged out."
    )
    flash("You have been securely logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "update_info":
            name = request.form.get("name", "").strip()
            phone = request.form.get("phone", "").strip()
            if name:
                current_user.name = name
                current_user.phone = phone or None
                db.session.commit()
                flash("Profile details updated successfully.", "success")
                SecurityService.log_event(
                    action="PROFILE_UPDATED",
                    target_type="User",
                    target_id=current_user.id,
                    actor_id=current_user.id,
                    details="Updated name and phone contact."
                )

        elif action == "change_password":
            current_pw = request.form.get("current_password", "")
            new_pw = request.form.get("new_password", "")
            confirm_pw = request.form.get("confirm_password", "")

            if not current_user.check_password(current_pw):
                flash("Current password is incorrect.", "danger")
            elif len(new_pw) < 8:
                flash("New password must be at least 8 characters long.", "danger")
            elif new_pw != confirm_pw:
                flash("New passwords do not match.", "danger")
            else:
                current_user.set_password(new_pw)
                db.session.commit()
                flash("Password changed successfully.", "success")
                SecurityService.log_event(
                    action="PASSWORD_CHANGED",
                    target_type="User",
                    target_id=current_user.id,
                    actor_id=current_user.id,
                    details="Password updated."
                )

        elif action == "update_pin":
            new_pin = request.form.get("pin", "").strip()
            if new_pin and (not new_pin.isdigit() or len(new_pin) < 4 or len(new_pin) > 6):
                flash("Alternative PIN must be 4 to 6 numeric digits.", "danger")
            else:
                current_user.set_pin(new_pin if new_pin else None)
                db.session.commit()
                msg = "Alternative verification PIN set successfully." if new_pin else "Alternative PIN removed."
                flash(msg, "success")
                SecurityService.log_event(
                    action="PIN_UPDATED",
                    target_type="User",
                    target_id=current_user.id,
                    actor_id=current_user.id,
                    details="Alternative verification PIN updated."
                )

        return redirect(url_for("auth.profile"))

    return render_template("profile.html", user=current_user)
