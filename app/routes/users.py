from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.extensions import db
from app.models.user import User
from app.models.department import Department
from app.models.face import FaceEnrollment
from app.services.security_service import SecurityService

users_bp = Blueprint("users", __name__, url_prefix="/users")


@users_bp.route("")
@login_required
def list_users():
    # Only staff or admins can view full user directory
    if not current_user.is_staff:
        flash("Access restricted to staff and administrators.", "warning")
        return redirect(url_for("dashboard.index"))

    query = User.query

    # Search filter
    search = request.args.get("q", "").strip()
    if search:
        query = query.filter(
            (User.name.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
        )

    # Department filter
    dept_id = request.args.get("dept")
    if dept_id and dept_id.isdigit():
        query = query.filter(User.department_id == int(dept_id))

    # Role filter
    role = request.args.get("role")
    if role in ("admin", "staff", "user"):
        query = query.filter(User.role == role)

    # Status filter
    status = request.args.get("status")
    if status in ("active", "inactive", "suspended"):
        query = query.filter(User.status == status)

    # Enrollment filter
    enrolled = request.args.get("enrolled")
    if enrolled == "yes":
        query = query.join(FaceEnrollment).filter(FaceEnrollment.is_active == True)
    elif enrolled == "no":
        query = query.outerjoin(FaceEnrollment).filter(
            (FaceEnrollment.id == None) | (FaceEnrollment.is_active == False)
        )

    users = query.order_by(User.name.asc()).all()
    departments = Department.query.order_by(Department.name.asc()).all()

    return render_template(
        "users/list.html",
        users=users,
        departments=departments,
        current_filters={
            "q": search,
            "dept": dept_id,
            "role": role,
            "status": status,
            "enrolled": enrolled,
        }
    )


@users_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_user():
    if not current_user.is_admin:
        flash("Only administrators are authorized to add new users.", "danger")
        return redirect(url_for("users.list_users"))

    departments = Department.query.order_by(Department.name.asc()).all()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        department_id = request.form.get("department_id")
        role = request.form.get("role", "user")
        password = request.form.get("password", "")
        pin = request.form.get("pin", "").strip()

        if not name or not email or not password:
            flash("Full Name, Email, and Password are required.", "danger")
            return render_template("users/add.html", departments=departments)

        existing = User.query.filter_by(email=email).first()
        if existing:
            flash(f"User with email '{email}' already exists.", "danger")
            return render_template("users/add.html", departments=departments)

        user = User(
            name=name,
            email=email,
            phone=phone or None,
            department_id=int(department_id) if department_id and department_id.isdigit() else None,
            role=role if role in ("admin", "staff", "user") else "user",
            status="active",
        )
        user.set_password(password)
        if pin and pin.isdigit():
            user.set_pin(pin)

        db.session.add(user)
        db.session.commit()

        SecurityService.log_event(
            action="USER_CREATED",
            target_type="User",
            target_id=user.id,
            actor_id=current_user.id,
            details=f"Admin created user: {user.name} ({user.email}) with role '{user.role}'."
        )

        flash(f"User '{user.name}' has been created successfully.", "success")
        return redirect(url_for("users.list_users"))

    return render_template("users/add.html", departments=departments)


@users_bp.route("/<int:user_id>")
@login_required
def view_user(user_id):
    # Only staff/admins or the user themselves can view this profile
    if not current_user.is_staff and current_user.id != user_id:
        flash("Access denied.", "danger")
        return redirect(url_for("dashboard.index"))

    user = User.query.get_or_404(user_id)
    return render_template("users/view.html", user=user)


@users_bp.route("/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def edit_user(user_id):
    if not current_user.is_admin:
        flash("Only administrators can edit user profiles.", "danger")
        return redirect(url_for("users.list_users"))

    user = User.query.get_or_404(user_id)
    departments = Department.query.order_by(Department.name.asc()).all()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        department_id = request.form.get("department_id")
        role = request.form.get("role", user.role)
        status = request.form.get("status", user.status)
        new_password = request.form.get("new_password", "")
        new_pin = request.form.get("new_pin", "").strip()

        # Check email uniqueness
        if email != user.email:
            existing = User.query.filter_by(email=email).first()
            if existing:
                flash(f"Email '{email}' is already in use by another user.", "danger")
                return render_template("users/edit.html", user=user, departments=departments)

        user.name = name
        user.email = email
        user.phone = phone or None
        user.department_id = int(department_id) if department_id and department_id.isdigit() else None
        user.role = role
        user.status = status

        if new_password:
            user.set_password(new_password)
        if new_pin is not None:
            if new_pin == "":
                user.pin_hash = None
            elif new_pin.isdigit() and len(new_pin) >= 4:
                user.set_pin(new_pin)

        db.session.commit()

        SecurityService.log_event(
            action="USER_UPDATED",
            target_type="User",
            target_id=user.id,
            actor_id=current_user.id,
            details=f"Admin updated profile for {user.email} (Role: {user.role}, Status: {user.status})."
        )

        flash(f"User '{user.name}' updated successfully.", "success")
        return redirect(url_for("users.view_user", user_id=user.id))

    return render_template("users/edit.html", user=user, departments=departments)


@users_bp.route("/<int:user_id>/delete", methods=["POST"])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash("Only administrators can delete user accounts.", "danger")
        return redirect(url_for("users.list_users"))

    if current_user.id == user_id:
        flash("You cannot delete your own administrative account.", "danger")
        return redirect(url_for("users.list_users"))

    user = User.query.get_or_404(user_id)
    name = user.name
    email = user.email

    db.session.delete(user)
    db.session.commit()

    SecurityService.log_event(
        action="USER_DELETED",
        target_type="User",
        target_id=user_id,
        actor_id=current_user.id,
        details=f"Admin deleted user {name} ({email}) and purged all associated biometric templates."
    )

    flash(f"User '{name}' and all associated biometric records have been permanently deleted.", "success")
    return redirect(url_for("users.list_users"))


@users_bp.route("/<int:user_id>/delete-face", methods=["POST"])
@login_required
def delete_face(user_id):
    # Only admin or the user themselves can delete facial enrollment
    if not current_user.is_admin and current_user.id != user_id:
        flash("Access denied.", "danger")
        return redirect(url_for("dashboard.index"))

    user = User.query.get_or_404(user_id)
    if user.face_enrollment:
        db.session.delete(user.face_enrollment)
        db.session.commit()

        SecurityService.log_event(
            action="BIOMETRIC_DELETED",
            target_type="FaceEnrollment",
            target_id=user.id,
            actor_id=current_user.id,
            details=f"Face biometric enrollment deleted/revoked for user {user.name}."
        )
        flash("Facial biometric enrollment successfully deleted.", "info")
    else:
        flash("No active facial enrollment found for this user.", "warning")

    return redirect(url_for("users.view_user", user_id=user.id))
