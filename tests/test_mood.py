import pytest
import numpy as np
from PIL import Image, ImageDraw
from app.services.mood_service import MoodService
from app.services.face_service import FaceService
from app.models.mood_log import MoodLog
from app.extensions import db


def create_synthetic_face(expression="happy"):
    img = Image.new("RGB", (320, 240), color=(190, 205, 220))
    d = ImageDraw.Draw(img)
    # Face oval
    d.ellipse([100, 40, 220, 200], fill=(230, 190, 160))
    # Eyes
    d.ellipse([125, 90, 145, 110], fill=(40, 30, 20))
    d.ellipse([175, 90, 195, 110], fill=(40, 30, 20))

    if expression == "happy":
        d.arc([130, 140, 190, 180], start=0, end=180, fill=(180, 50, 50), width=4)
    elif expression == "surprised":
        d.ellipse([145, 145, 175, 185], fill=(160, 50, 50))
    elif expression == "stressed":
        # Brow lines
        d.line([120, 80, 145, 90], fill=(40, 30, 20), width=3)
        d.line([175, 90, 200, 80], fill=(40, 30, 20), width=3)
        # Tense mouth
        d.line([135, 160, 185, 160], fill=(160, 50, 50), width=4)
    else:
        d.line([135, 155, 185, 155], fill=(170, 60, 60), width=3)
    return img


def test_mood_service_analysis(app):
    """Verify facial mood analysis computes valid telemetry and normalized breakdown."""
    with app.app_context():
        face_img = create_synthetic_face("happy")
        res = MoodService.analyze_face_mood(face_img)

        assert res["face_detected"] is True
        assert res["dominant_mood"] in MoodService.EMOTION_PROFILES
        assert 0.0 <= res["confidence"] <= 100.0
        assert -1.0 <= res["valence"] <= 1.0
        assert 0.0 <= res["arousal"] <= 1.0
        assert isinstance(res["breakdown"], dict)
        assert len(res["breakdown"]) == 7
        assert "wellness_tip" in res


def test_mood_service_blank_frame(app):
    """Verify black frame gracefully returns no face detected status."""
    with app.app_context():
        blank = np.zeros((120, 160, 3), dtype=np.uint8)
        res = MoodService.analyze_face_mood(blank)
        assert res["face_detected"] is False
        assert res["dominant_mood"] == "neutral"


def test_log_mood_and_analytics(app, seed_data):
    """Verify logging mood check-ins and aggregating analytics."""
    with app.app_context():
        admin = seed_data["admin"]
        mood_data = {
            "dominant_mood": "happy",
            "feeling_tag": "Radiant & Cheerful",
            "emoji": "😊",
            "confidence": 92.5,
            "valence": 0.85,
            "arousal": 0.70,
            "breakdown": {"happy": 92.5, "calm": 5.0, "neutral": 2.5}
        }
        log = MoodService.log_mood(
            user_id=admin.id,
            mood_data=mood_data,
            note="Team standup win",
            context="camera_tracker"
        )
        assert log.id is not None
        assert log.dominant_mood == "happy"
        assert log.user_id == admin.id

        analytics = MoodService.get_mood_analytics(user_id=admin.id, days=7)
        assert analytics["total_checkins"] >= 1
        assert "wellness_index" in analytics
        assert analytics["distribution"]["happy"] >= 1


def test_mood_http_endpoints(client, seed_data):
    """Verify mood tracker pages and API endpoints with authenticated session."""
    # Log in as admin
    client.post("/login", data={"email": "admin@test.local", "password": "AdminPass123!"})

    # Tracker page
    res = client.get("/mood")
    assert res.status_code == 200
    assert b"AI Face Mood" in res.data

    # Analytics page
    res_analytics = client.get("/mood/analytics")
    assert res_analytics.status_code == 200
    assert b"Emotional Wellness" in res_analytics.data

    # History API
    res_hist = client.get("/mood/api/history?days=7")
    assert res_hist.status_code == 200
    json_data = res_hist.get_json()
    assert json_data["success"] is True

    # Log Mood API
    res_log = client.post("/mood/api/log", json={
        "mood_data": {
            "dominant_mood": "calm",
            "feeling_tag": "Peaceful & Grounded",
            "emoji": "😌",
            "confidence": 88.0,
            "valence": 0.60,
            "arousal": 0.25,
            "breakdown": {"calm": 88.0, "neutral": 12.0}
        },
        "note": "Meditation completed"
    })
    assert res_log.status_code == 201
    assert res_log.get_json()["success"] is True


def test_multi_person_mood_analysis(app, monkeypatch):
    """Verify system can detect and analyze multiple persons in the same camera frame."""
    with app.app_context():
        dual_img = Image.new("RGB", (480, 240), color=(190, 205, 220))
        d = ImageDraw.Draw(dual_img)
        d.ellipse([50, 40, 170, 200], fill=(230, 190, 160))
        d.ellipse([270, 40, 390, 200], fill=(225, 185, 155))

        monkeypatch.setattr(
            FaceService,
            "detect_faces",
            lambda img: [
                {"x": 50, "y": 40, "w": 120, "h": 160, "confidence": 0.95},
                {"x": 270, "y": 40, "w": 120, "h": 160, "confidence": 0.92}
            ]
        )

        res = MoodService.analyze_face_mood(dual_img)
        assert res["face_detected"] is True
        assert res["face_count"] == 2
        assert len(res["faces"]) == 2
        assert res["faces"][0]["person_id"] == 1
        assert res["faces"][1]["person_id"] == 2
        assert "dominant_mood" in res["faces"][0]
        assert "wellness_tip" in res["faces"][0]
        assert "group_summary" in res


def test_capture_and_save_mood_picture(client, app, seed_data):
    """Verify captured face picture is compressed and saved to database during mood logging."""
    import base64
    import io

    # Create test synthetic face and encode to base64
    img = create_synthetic_face("happy")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    b64_str = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")

    # Log in as admin
    client.post("/login", data={"email": "admin@test.local", "password": "AdminPass123!"})

    # Call /mood/api/log with image
    res = client.post("/mood/api/log", json={
        "mood_data": {
            "dominant_mood": "happy",
            "feeling_tag": "Radiant & Cheerful",
            "emoji": "😊",
            "confidence": 95.0,
            "valence": 0.85,
            "arousal": 0.70,
            "breakdown": {"happy": 95.0, "calm": 5.0}
        },
        "image": b64_str,
        "note": "Snapshot with camera photo"
    })
    assert res.status_code == 201
    json_data = res.get_json()
    assert json_data["success"] is True
    assert "log" in json_data
    assert json_data["log"]["captured_image"] is not None
    assert json_data["log"]["captured_image"].startswith("data:image/jpeg;base64,")

    # Verify directly in database
    with app.app_context():
        log_in_db = MoodLog.query.get(json_data["log"]["id"])
        assert log_in_db is not None
        assert log_in_db.captured_image is not None
        assert log_in_db.captured_image.startswith("data:image/jpeg;base64,")


def test_one_time_snapshot_per_person(app):
    """
    Verify auto-capture takes snapshot ONLY 1 time for a person,
    then scans mood only without duplicate snapshots for returning faces.
    """
    import io
    import base64

    with app.app_context():
        MoodService.reset_captured_persons()

        # 1. First time Person 1 appears
        face1 = create_synthetic_face("happy")
        res1 = MoodService.analyze_face_mood(face1)
        assert res1["face_detected"] is True
        assert res1["needs_snapshot"] is True
        assert res1["has_new_person"] is True
        assert res1["faces"][0]["is_new_person"] is True
        assert res1["faces"][0]["needs_snapshot"] is True

        # 2. Save 1-time snapshot for Person 1
        buf = io.BytesIO()
        face1.save(buf, format="JPEG")
        b64_str = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")

        log1 = MoodService.log_mood(
            user_id=None,
            mood_data=res1["faces"][0],
            captured_image=b64_str,
            context="camera_auto_capture"
        )
        assert log1.captured_image is not None
        assert MoodService.get_captured_persons_count() == 1

        # 3. Second time same Person 1 appears
        res2 = MoodService.analyze_face_mood(face1)
        assert res2["face_detected"] is True
        assert res2["needs_snapshot"] is False
        assert res2["has_new_person"] is False
        assert res2["faces"][0]["is_new_person"] is False
        assert res2["faces"][0]["needs_snapshot"] is False

        # 4. Subsequent log for known person: mood only, NO snapshot
        log2 = MoodService.log_mood(
            user_id=None,
            mood_data=res2["faces"][0],
            captured_image=None,
            context="camera_auto_capture (mood only)"
        )
        assert log2.captured_image is None
        assert log2.dominant_mood == res2["faces"][0]["dominant_mood"]


def test_new_person_snapshot_and_reset(client, app, seed_data):
    """
    Verify when a new person arrives, the system takes a snapshot for the new person,
    and verify reset API clears memory for fresh captures.
    """
    import io
    import base64

    with app.app_context():
        MoodService.reset_captured_persons()

        # Face 1 (Person 1)
        face1 = create_synthetic_face("happy")
        res1 = MoodService.analyze_face_mood(face1)

        buf1 = io.BytesIO()
        face1.save(buf1, format="JPEG")
        b64_1 = "data:image/jpeg;base64," + base64.b64encode(buf1.getvalue()).decode("ascii")
        MoodService.log_mood(None, res1["faces"][0], captured_image=b64_1)

        # Face 2 (Person 2 - distinctly different face)
        face2 = Image.new("RGB", (320, 240), color=(110, 130, 150))
        d2 = ImageDraw.Draw(face2)
        d2.ellipse([70, 30, 190, 190], fill=(110, 70, 50))
        d2.ellipse([95, 80, 115, 100], fill=(20, 20, 20))
        d2.ellipse([145, 80, 165, 100], fill=(20, 20, 20))
        d2.line([100, 140, 160, 140], fill=(70, 20, 20), width=4)

        res2 = MoodService.analyze_face_mood(face2)
        assert res2["face_detected"] is True
        assert res2["has_new_person"] is True
        assert res2["needs_snapshot"] is True
        assert res2["faces"][0]["is_new_person"] is True

        # Save snapshot for new person
        buf2 = io.BytesIO()
        face2.save(buf2, format="JPEG")
        b64_2 = "data:image/jpeg;base64," + base64.b64encode(buf2.getvalue()).decode("ascii")
        log_new = MoodService.log_mood(None, res2["faces"][0], captured_image=b64_2)
        assert log_new.captured_image is not None
        assert MoodService.get_captured_persons_count() == 2

    # Test reset API via authenticated client
    client.post("/login", data={"email": "admin@test.local", "password": "AdminPass123!"})
    res_stats = client.get("/mood/api/captured-stats")
    assert res_stats.status_code == 200
    assert res_stats.get_json()["captured_count"] == 2

    res_reset = client.post("/mood/api/reset-captured")
    assert res_reset.status_code == 200
    assert res_reset.get_json()["success"] is True

    res_stats2 = client.get("/mood/api/captured-stats")
    assert res_stats2.status_code == 200
    assert res_stats2.get_json()["captured_count"] == 0


