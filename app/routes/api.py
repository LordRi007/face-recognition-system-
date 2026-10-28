import logging
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_user, logout_user, current_user, login_required
from app.extensions import db, csrf
from app.models.user import User
from app.models.face import FaceEnrollment
from app.models.attendance import Attendance, VerificationLog
from app.services.face_service import FaceService
from app.services.security_service import SecurityService
from app.services.attendance_service import AttendanceService
from app.services.report_service import ReportService

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__, url_prefix="/api")

# Exempt API endpoints from CSRF if called with programmatic JSON headers
# (Web forms still use CSRF tokens)
csrf.exempt(api_bp)


# ============================================================================
# Authentication Endpoints
# ============================================================================

@api_bp.route("/auth/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or request.form
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"success": False, "error": "Email and password are required."}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        SecurityService.log_event("API_LOGIN_FAILED", "User", details=f"Unknown email: {email}")
        return jsonify({"success": False, "error": "Invalid email or password."}), 401

    if user.is_locked():
        return jsonify({
            "success": False,
            "error": "Account is temporarily locked due to excessive failed attempts."
        }), 403

    if user.status != "active":
        return jsonify({"success": False, "error": "Account is not active."}), 403

    if not user.check_password(password):
        max_attempts = current_app.config.get("RATE_LIMIT_LOGIN_ATTEMPTS", 5)
        lockout_mins = current_app.config.get("RATE_LIMIT_LOCKOUT_MINUTES", 15)
        user.record_failed_login(max_attempts=max_attempts, lockout_minutes=lockout_mins)
        return jsonify({"success": False, "error": "Invalid email or password."}), 401

    user.reset_failed_logins()
    login_user(user)

    SecurityService.log_event("API_LOGIN_SUCCESS", "User", target_id=user.id, actor_id=user.id)
    return jsonify({
        "success": True,
        "message": f"Authenticated successfully as {user.name}.",
        "user": user.to_dict()
    }), 200


@api_bp.route("/auth/logout", methods=["POST"])
@login_required
def api_logout():
    user_id = current_user.id
    logout_user()
    SecurityService.log_event("API_LOGOUT", "User", target_id=user_id, actor_id=user_id)
    return jsonify({"success": True, "message": "Logged out successfully."}), 200


# ============================================================================
# User Management Endpoints
# ============================================================================

@api_bp.route("/users", methods=["GET"])
@login_required
def api_get_users():
    if not current_user.is_staff:
        return jsonify({"success": False, "error": "Access denied."}), 403

    users = User.query.order_by(User.name.asc()).all()
    return jsonify({
        "success": True,
        "count": len(users),
        "users": [u.to_dict() for u in users]
    }), 200


@api_bp.route("/users", methods=["POST"])
@login_required
def api_create_user():
    if not current_user.is_admin:
        return jsonify({"success": False, "error": "Only administrators can create users."}), 403

    data = request.get_json(silent=True) or request.form
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    role = data.get("role", "user")
    department_id = data.get("department_id")
    phone = data.get("phone", "").strip()
    pin = data.get("pin", "").strip()

    if not name or not email or not password:
        return jsonify({"success": False, "error": "Name, email, and password are required."}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"success": False, "error": f"Email '{email}' is already registered."}), 409

    new_user = User(
        name=name,
        email=email,
        phone=phone or None,
        role=role if role in ("admin", "staff", "user") else "user",
        department_id=int(department_id) if department_id else None,
        status="active"
    )
    new_user.set_password(password)
    if pin and pin.isdigit():
        new_user.set_pin(pin)

    db.session.add(new_user)
    db.session.commit()

    SecurityService.log_event(
        "API_USER_CREATED", "User", target_id=new_user.id, actor_id=current_user.id,
        details=f"Created user {name} ({email})"
    )

    return jsonify({"success": True, "user": new_user.to_dict()}), 201


@api_bp.route("/users/<int:user_id>", methods=["GET"])
@login_required
def api_get_user(user_id):
    if not current_user.is_staff and current_user.id != user_id:
        return jsonify({"success": False, "error": "Access denied."}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "error": "User not found."}), 404

    return jsonify({"success": True, "user": user.to_dict(include_sensitive=current_user.is_admin)}), 200


@api_bp.route("/users/<int:user_id>", methods=["PUT"])
@login_required
def api_update_user(user_id):
    if not current_user.is_admin:
        return jsonify({"success": False, "error": "Only administrators can update users."}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "error": "User not found."}), 404

    data = request.get_json(silent=True) or request.form
    if "name" in data:
        user.name = data["name"].strip()
    if "phone" in data:
        user.phone = data["phone"].strip() or None
    if "department_id" in data:
        user.department_id = int(data["department_id"]) if data["department_id"] else None
    if "role" in data and data["role"] in ("admin", "staff", "user"):
        user.role = data["role"]
    if "status" in data and data["status"] in ("active", "inactive", "suspended"):
        user.status = data["status"]
    if "password" in data and data["password"]:
        user.set_password(data["password"])
    if "pin" in data:
        pin = str(data["pin"]).strip()
        user.set_pin(pin if pin else None)

    db.session.commit()
    SecurityService.log_event(
        "API_USER_UPDATED", "User", target_id=user.id, actor_id=current_user.id
    )

    return jsonify({"success": True, "user": user.to_dict()}), 200


@api_bp.route("/users/<int:user_id>", methods=["DELETE"])
@login_required
def api_delete_user(user_id):
    if not current_user.is_admin:
        return jsonify({"success": False, "error": "Only administrators can delete users."}), 403

    if current_user.id == user_id:
        return jsonify({"success": False, "error": "Cannot delete your own administrative account."}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "error": "User not found."}), 404

    name = user.name
    db.session.delete(user)
    db.session.commit()

    SecurityService.log_event(
        "API_USER_DELETED", "User", target_id=user_id, actor_id=current_user.id,
        details=f"Permanently deleted user '{name}' and purged biometric embeddings."
    )

    return jsonify({"success": True, "message": f"User '{name}' deleted successfully."}), 200


# ============================================================================
# Live Face Detection & Quality Feedback Endpoint
# ============================================================================

@api_bp.route("/face/detect", methods=["POST"])
@login_required
def api_face_detect():
    """Validates live video frames and returns face count, blur, and lighting metrics."""
    data = request.get_json(silent=True) or {}
    image_data = data.get("image")
    if not image_data:
        return jsonify({"success": False, "error": "No image data received."}), 400

    try:
        cv_img = FaceService.decode_base64_image(image_data)
        quality = FaceService.validate_quality(cv_img)
        faces = FaceService.detect_faces(cv_img)

        return jsonify({
            "success": True,
            "face_count": len(faces),
            "faces": faces,
            "quality": quality,
            "is_ready_for_enrollment": (len(faces) == 1 and quality["passed"])
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# ============================================================================
# Face Enrollment & Verification Endpoints
# ============================================================================

@api_bp.route("/face/enroll", methods=["POST"])
@login_required
def api_face_enroll():
    """
    Enrolls a user's facial biometric template with mandatory informed consent.
    Captures image, performs quality & single-face validation, extracts FaceNet512 embedding,
    encrypts it with AES/Fernet, and stores metadata.
    """
    data = request.get_json(silent=True) or {}
    target_user_id = data.get("user_id", current_user.id)
    consent_agreed = data.get("consent_agreed", False)
    image_data = data.get("image")

    # Consent verification
    if not consent_agreed:
        return jsonify({
            "success": False,
            "error": "Explicit informed biometric consent is mandatory prior to facial enrollment."
        }), 400

    # Authorization
    if not current_user.is_staff and current_user.id != int(target_user_id):
        return jsonify({"success": False, "error": "Access denied. You may only enroll your own biometric data."}), 403

    user = User.query.get(target_user_id)
    if not user:
        return jsonify({"success": False, "error": "User not found."}), 404

    if not image_data:
        return jsonify({"success": False, "error": "No image data provided for enrollment."}), 400

    try:
        cv_img = FaceService.decode_base64_image(image_data)
        
        # 1. Quality validation
        quality = FaceService.validate_quality(cv_img)
        if not quality["passed"]:
            return jsonify({
                "success": False,
                "error": "Image quality insufficient: " + " ".join(quality["issues"]),
                "quality": quality
            }), 422

        # 2. Face count check (must be exactly 1)
        faces = FaceService.detect_faces(cv_img)
        if len(faces) == 0:
            return jsonify({
                "success": False,
                "error": "No face detected in enrollment frame. Please center your face.",
                "quality": quality
            }), 422
        elif len(faces) > 1:
            return jsonify({
                "success": False,
                "error": f"Multiple faces ({len(faces)}) detected. Only one person must be present.",
                "quality": quality
            }), 422

        # 3. Anti-spoofing heuristic
        liveness = FaceService.check_liveness_heuristic(cv_img, faces[0])
        if not liveness["is_live"]:
            return jsonify({
                "success": False,
                "error": liveness["reason"],
                "quality": quality
            }), 422

        # 4. Extract ArcFace 512-D deep embedding from the cropped primary face
        embedding = FaceService.extract_embedding(cv_img, face_box=faces[0])

        # 5. Encrypt embedding using Fernet AES
        encrypted_embedding = SecurityService.encrypt_embedding(embedding)

        # 6. Save or update enrollment
        model_name = current_app.config.get("FACENET_MODEL_NAME", "Facenet512")
        enrollment = FaceEnrollment.query.filter_by(user_id=user.id).first()
        if not enrollment:
            enrollment = FaceEnrollment(
                user_id=user.id,
                encrypted_embedding=encrypted_embedding,
                model_name=model_name,
                model_version="1.0",
                embedding_dimension=len(embedding),
                samples_count=1,
                quality_score=quality["blur_score"],
                consent_version="1.0",
                consent_timestamp=datetime.now(timezone.utc),
                is_active=True
            )
            db.session.add(enrollment)
        else:
            enrollment.encrypted_embedding = encrypted_embedding
            enrollment.model_name = model_name
            enrollment.samples_count += 1
            enrollment.quality_score = quality["blur_score"]
            enrollment.consent_timestamp = datetime.now(timezone.utc)
            enrollment.is_active = True

        db.session.commit()

        SecurityService.log_event(
            action="BIOMETRIC_ENROLLED",
            target_type="FaceEnrollment",
            target_id=user.id,
            actor_id=current_user.id,
            details=f"Facial biometric enrolled with consent for user {user.name} ({model_name})."
        )

        return jsonify({
            "success": True,
            "message": f"Face successfully enrolled for {user.name}!",
            "enrollment": enrollment.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Enrollment failure: {e}")
        return jsonify({"success": False, "error": f"Enrollment failed: {str(e)}"}), 500


@api_bp.route("/face/verify", methods=["POST"])
@login_required
def api_face_verify():
    """
    Executes consent-based 1-to-1 facial verification against the claimed user's stored template.
    Records verification outcome without exposing raw biometric data.
    """
    data = request.get_json(silent=True) or {}
    claimed_user_id = data.get("user_id")
    image_data = data.get("image")
    verification_method = data.get("method", "webcam")
    pin = data.get("pin")

    if not claimed_user_id:
        return jsonify({"success": False, "error": "Claimed user ID is required for 1-to-1 verification."}), 400

    # Authorization check: only staff can verify other users; users verify themselves
    if not current_user.is_staff and current_user.id != int(claimed_user_id):
        return jsonify({"success": False, "error": "Access denied."}), 403

    user = User.query.get(claimed_user_id)
    if not user:
        return jsonify({"success": False, "error": "Claimed user does not exist."}), 404

    # Option A: Alternative PIN Verification (non-biometric fallback)
    if pin:
        is_pin_valid = user.check_pin(str(pin))
        v_log = VerificationLog(
            user_id=user.id,
            result="success" if is_pin_valid else "failure",
            verification_method="alternative_pin",
            error_code=None if is_pin_valid else "INVALID_PIN",
            ip_address=SecurityService.get_client_ip()
        )
        db.session.add(v_log)
        db.session.commit()

        if is_pin_valid:
            return jsonify({
                "verified": True,
                "user": user.to_dict(),
                "method": "alternative_pin",
                "message": "Alternative PIN verification successful!"
            }), 200
        else:
            return jsonify({
                "verified": False,
                "error": "Incorrect alternative PIN. Please try again.",
                "method": "alternative_pin"
            }), 401

    # Option B: Facial Biometric Verification
    if not user.has_face_enrolled:
        return jsonify({
            "success": False,
            "error": f"User {user.name} does not have an enrolled facial template. Please enroll first or use PIN."
        }), 400

    if not image_data:
        return jsonify({"success": False, "error": "No image data received for verification."}), 400

    try:
        cv_img = FaceService.decode_base64_image(image_data)
        
        # Execute 1-to-1 verification
        verification = FaceService.verify_one_to_one(
            presented_image=cv_img,
            enrolled_encrypted_embedding=user.face_enrollment.encrypted_embedding
        )

        # Log verification outcome (strict privacy: NEVER store raw images or embeddings)
        v_log = VerificationLog(
            user_id=user.id,
            result=verification["result"],
            verification_method=verification_method,
            distance_score=verification.get("distance"),
            threshold_used=verification.get("threshold"),
            error_code=verification.get("error_code"),
            ip_address=SecurityService.get_client_ip()
        )
        db.session.add(v_log)
        db.session.commit()

        return jsonify({
            "verified": verification["verified"],
            "result": verification["result"],
            "message": verification["message"],
            "distance": verification.get("distance"),
            "threshold": verification.get("threshold"),
            "similarity_pct": verification.get("similarity_pct"),
            "quality": verification.get("quality"),
            "user": user.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Verification route error: {e}")
        return jsonify({"success": False, "error": f"Verification failed: {str(e)}"}), 500


@api_bp.route("/face/enrollment", methods=["DELETE"])
@login_required
def api_delete_enrollment():
    """Deletes/un-enrolls facial biometric data for a user upon request."""
    data = request.get_json(silent=True) or {}
    target_user_id = data.get("user_id", current_user.id)

    if not current_user.is_admin and current_user.id != int(target_user_id):
        return jsonify({"success": False, "error": "Access denied."}), 403

    user = User.query.get(target_user_id)
    if not user or not user.face_enrollment:
        return jsonify({"success": False, "error": "No active biometric enrollment found."}), 404

    db.session.delete(user.face_enrollment)
    db.session.commit()

    SecurityService.log_event(
        action="API_BIOMETRIC_DELETED",
        target_type="FaceEnrollment",
        target_id=user.id,
        actor_id=current_user.id,
        details=f"Revoked and purged facial biometrics for user {user.name}."
    )

    return jsonify({"success": True, "message": "Biometric enrollment successfully deleted."}), 200


# ============================================================================
# Attendance Endpoints
# ============================================================================

@api_bp.route("/attendance", methods=["GET"])
@login_required
def api_get_attendance():
    date_str = request.args.get("date")
    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            target_date = datetime.now(timezone.utc).date()
    else:
        target_date = datetime.now(timezone.utc).date()

    query = Attendance.query.filter_by(date=target_date)
    if not current_user.is_staff:
        query = query.filter_by(user_id=current_user.id)

    records = query.all()
    return jsonify({
        "success": True,
        "date": target_date.isoformat(),
        "records": [r.to_dict() for r in records]
    }), 200


@api_bp.route("/attendance/check-in", methods=["POST"])
@login_required
def api_attendance_checkin():
    data = request.get_json(silent=True) or request.form
    user_id = data.get("user_id", current_user.id)
    method = data.get("method", "facial")
    notes = data.get("notes")

    if not current_user.is_staff and current_user.id != int(user_id):
        return jsonify({"success": False, "error": "Access denied."}), 403

    result = AttendanceService.process_check_in(
        user_id=int(user_id),
        verification_method=method,
        custom_notes=notes
    )

    status_code = 200 if result["success"] else 400
    return jsonify(result), status_code


@api_bp.route("/attendance/check-out", methods=["POST"])
@login_required
def api_attendance_checkout():
    data = request.get_json(silent=True) or request.form
    user_id = data.get("user_id", current_user.id)
    method = data.get("method", "facial")
    notes = data.get("notes")

    if not current_user.is_staff and current_user.id != int(user_id):
        return jsonify({"success": False, "error": "Access denied."}), 403

    result = AttendanceService.process_check_out(
        user_id=int(user_id),
        verification_method=method,
        custom_notes=notes
    )

    status_code = 200 if result["success"] else 400
    return jsonify(result), status_code


# ============================================================================
# Reports & Dashboard Analytics Endpoints
# ============================================================================

@api_bp.route("/reports/attendance", methods=["GET"])
@login_required
def api_reports_attendance():
    if not current_user.is_staff:
        return jsonify({"success": False, "error": "Access denied."}), 403

    trends = ReportService.get_attendance_trends(days=14)
    breakdown = ReportService.get_verification_breakdown()
    dept_stats = ReportService.get_department_stats()

    return jsonify({
        "success": True,
        "trends": trends,
        "verification_breakdown": breakdown,
        "department_stats": dept_stats
    }), 200


@api_bp.route("/dashboard/statistics", methods=["GET"])
@login_required
def api_dashboard_statistics():
    metrics = ReportService.get_dashboard_metrics()
    trends = ReportService.get_attendance_trends(days=7)
    return jsonify({
        "success": True,
        "metrics": metrics,
        "trends": trends
    }), 200
