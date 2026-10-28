import logging
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.extensions import csrf
from app.services.face_service import FaceService
from app.services.mood_service import MoodService
from app.models.mood_log import MoodLog
from app.models.user import User

logger = logging.getLogger(__name__)

mood_bp = Blueprint("mood", __name__, url_prefix="/mood")
csrf.exempt(mood_bp)


@mood_bp.route("")
@mood_bp.route("/tracker")
@login_required
def tracker():
    """Live Camera Face Mood & Feeling Tracker interactive HUD."""
    recent_logs = (
        MoodLog.query.filter_by(user_id=current_user.id)
        .order_by(MoodLog.timestamp.desc())
        .limit(8)
        .all()
    )
    return render_template(
        "mood/tracker.html",
        recent_logs=recent_logs,
        emotion_profiles=MoodService.EMOTION_PROFILES
    )


@mood_bp.route("/analytics")
@login_required
def analytics():
    """Emotional wellness insights and mood distribution trends."""
    user_id = None if current_user.is_admin and request.args.get("all") == "1" else current_user.id
    analytics_data = MoodService.get_mood_analytics(user_id=user_id, days=14)
    return render_template(
        "mood/analytics.html",
        analytics=analytics_data,
        emotion_profiles=MoodService.EMOTION_PROFILES,
        is_all_users=(user_id is None)
    )


# ============================================================================
# API Endpoints
# ============================================================================

@mood_bp.route("/api/analyze", methods=["POST"])
@login_required
def api_analyze_mood():
    """
    Real-time API endpoint for analyzing facial mood feeling from webcam frame.
    Accepts base64 image, returns live telemetry and emotion probabilities.
    """
    data = request.get_json(silent=True) or {}
    image_data = data.get("image")

    if not image_data:
        return jsonify({"success": False, "error": "No image frame received."}), 400

    try:
        cv_img = FaceService.decode_base64_image(image_data)
        analysis = MoodService.analyze_face_mood(cv_img)
        return jsonify({"success": True, "data": analysis}), 200
    except Exception as e:
        logger.error(f"Mood analysis API error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@mood_bp.route("/api/log", methods=["POST"])
@login_required
def api_log_mood():
    """Saves a facial mood check-in snapshot with optional user reflection note and captured picture."""
    data = request.get_json(silent=True) or {}
    mood_data = data.get("mood_data", {})
    note = data.get("note", "")
    context = data.get("context", "camera_tracker")
    captured_image = data.get("image") or data.get("captured_image") or mood_data.get("image")
    face_box = data.get("face_box") or mood_data.get("face_box")

    if not mood_data or not mood_data.get("dominant_mood"):
        return jsonify({"success": False, "error": "Invalid mood data."}), 400

    try:
        log_entry = MoodService.log_mood(
            user_id=current_user.id,
            mood_data=mood_data,
            note=note,
            context=context,
            captured_image=captured_image,
            face_box=face_box
        )
        return jsonify({
            "success": True,
            "message": f"Logged your mood as '{log_entry.feeling_tag}' {log_entry.emoji}!",
            "log": log_entry.to_dict(),
            "has_image": log_entry.captured_image is not None
        }), 201
    except Exception as e:
        logger.error(f"Error logging mood: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@mood_bp.route("/api/reset-captured", methods=["POST"])
@login_required
def api_reset_captured():
    """Resets memory of snapshotted persons so fresh snapshots can be captured."""
    MoodService.reset_captured_persons()
    return jsonify({
        "success": True,
        "message": "Snapshot memory reset. Auto-capture will take fresh snapshots for any detected person."
    }), 200


@mood_bp.route("/api/captured-stats", methods=["GET"])
@login_required
def api_captured_stats():
    """Returns number of unique persons currently snapshotted in memory."""
    return jsonify({
        "success": True,
        "captured_count": MoodService.get_captured_persons_count()
    }), 200


@mood_bp.route("/api/history", methods=["GET"])
@login_required
def api_mood_history():
    """Returns recent mood history for the current user."""
    days = request.args.get("days", default=7, type=int)
    analytics_data = MoodService.get_mood_analytics(user_id=current_user.id, days=days)
    return jsonify({"success": True, "analytics": analytics_data}), 200
