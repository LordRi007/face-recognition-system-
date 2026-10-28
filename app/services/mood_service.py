import io
import base64
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import numpy as np
from PIL import Image

from app.extensions import db
from app.models.mood_log import MoodLog
from app.models.user import User
from app.services.face_service import FaceService

logger = logging.getLogger(__name__)


class MoodService:
    """
    AI Computer Vision service for camera-based real-time facial mood and feeling tracking.
    Extracts facial Action Units (mouth curvature, smile intensity, brow furrow, eye alertness,
    jaw aperture) and maps them to psychological valence-arousal space and 7 core emotional states.
    """

    EMOTION_PROFILES = {
        "happy": {
            "name": "happy",
            "label": "Happy / Joyful",
            "emoji": "😊",
            "valence": 0.85,
            "arousal": 0.70,
            "color": "#10b981",  # Emerald Green
            "tag": "Radiant & Cheerful",
            "tip": "Fantastic energy! Great time to tackle creative brainstorms and collaborative projects."
        },
        "calm": {
            "name": "calm",
            "label": "Calm / Peaceful",
            "emoji": "😌",
            "valence": 0.60,
            "arousal": 0.25,
            "color": "#06b6d4",  # Cyan
            "tag": "Peaceful & Centered",
            "tip": "You are in a balanced, mindful zone. Ideal for strategic thinking and steady execution."
        },
        "focused": {
            "name": "focused",
            "label": "Focused / Engaged",
            "emoji": "🧐",
            "valence": 0.35,
            "arousal": 0.55,
            "color": "#6366f1",  # Indigo
            "tag": "Deep Focus & Flow",
            "tip": "Strong concentration detected. Keep notifications muted to protect your flow state."
        },
        "neutral": {
            "name": "neutral",
            "label": "Neutral / Balanced",
            "emoji": "😐",
            "valence": 0.05,
            "arousal": 0.35,
            "color": "#64748b",  # Slate
            "tag": "Balanced Baseline",
            "tip": "Calm and observant baseline. Take a breath and set your priority for the next hour."
        },
        "surprised": {
            "name": "surprised",
            "label": "Surprised / Alert",
            "emoji": "😲",
            "valence": 0.40,
            "arousal": 0.90,
            "color": "#f59e0b",  # Amber
            "tag": "High Alertness & Wonder",
            "tip": "High cognitive arousal detected. Channel this sensory alertness into solving tricky challenges."
        },
        "fatigued": {
            "name": "fatigued",
            "label": "Tired / Drowsy",
            "emoji": "🥱",
            "valence": -0.25,
            "arousal": 0.15,
            "color": "#8b5cf6",  # Purple
            "tag": "Fatigued / Low Energy",
            "tip": "Signs of ocular fatigue detected. Consider the 20-20-20 rule: rest eyes for 20 seconds, hydrate, or take a quick stretch."
        },
        "stressed": {
            "name": "stressed",
            "label": "Stressed / Tense",
            "emoji": "😣",
            "valence": -0.65,
            "arousal": 0.80,
            "color": "#ef4444",  # Red
            "tag": "High Tension / Stressed",
            "tip": "Facial muscle tension detected around brow/jaw. Take 3 slow, deep diaphragm breaths to lower cortisol."
        }
    }

    # In-memory registry of snapshotted persons for 1-time face snapshot auto-capture:
    # Each entry: {"person_id": int, "embedding": np.ndarray (512-D), "embeddings": List[np.ndarray], "captured_at": datetime, "sample_image": str, "name": str}
    _captured_persons: List[Dict[str, Any]] = []
    _next_person_id: int = 1
    # ArcFace cosine distance threshold: same person across poses is <= 0.48; different people are >= 0.65
    SAME_PERSON_THRESHOLD: float = 0.48
    _db_initialized: bool = False

    @classmethod
    def get_captured_persons_count(cls) -> int:
        """Returns the number of unique persons whose face snapshot has been saved."""
        return len(cls._captured_persons)

    @classmethod
    def reset_captured_persons(cls) -> None:
        """Clears memory of snapshotted persons so fresh snapshots can be taken."""
        cls._captured_persons = []
        cls._next_person_id = 1
        cls._db_initialized = True
        logger.info("Reset snapshotted persons registry.")

    @classmethod
    def _init_from_db_if_needed(cls) -> None:
        """Preloads recent snapshotted persons from database on startup so returning persons are verified."""
        if cls._db_initialized:
            return
        cls._db_initialized = True
        try:
            from flask import current_app
            if current_app and current_app.config.get("TESTING"):
                return
            from app.models.mood_log import MoodLog
            recent = MoodLog.query.filter(MoodLog.captured_image != None).order_by(MoodLog.id.desc()).limit(10).all()
            for r in reversed(recent):
                try:
                    cv = FaceService.decode_base64_image(r.captured_image)
                    e = FaceService.extract_embedding(cv)
                    cls.register_captured_person(e, sample_image=r.captured_image)
                except Exception:
                    pass
        except Exception:
            pass

    @classmethod
    def find_matching_captured_person(
        cls,
        embedding: Optional[np.ndarray],
        threshold: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Determines whether the presented face embedding matches any previously snapshotted person
        using ArcFace 512-D cosine distance.
        """
        if embedding is None:
            return None

        cls._init_from_db_if_needed()

        if not cls._captured_persons:
            return None

        if threshold is None:
            try:
                from flask import current_app
                if current_app:
                    threshold = current_app.config.get("SAME_PERSON_THRESHOLD", cls.SAME_PERSON_THRESHOLD)
                else:
                    threshold = cls.SAME_PERSON_THRESHOLD
            except Exception:
                threshold = cls.SAME_PERSON_THRESHOLD

        best_match = None
        min_dist = float("inf")

        for person in cls._captured_persons:
            embs = person.get("embeddings") or ([person.get("embedding")] if person.get("embedding") is not None else [])
            for pe in embs:
                dist = FaceService.compute_cosine_distance(embedding, pe)
                if dist < min_dist:
                    min_dist = dist
                    best_match = person

        if min_dist <= threshold:
            # If confirmed match, add embedding to person's cluster to adapt across poses/lighting
            if best_match and min_dist < 0.40:
                embs = best_match.setdefault("embeddings", [])
                if len(embs) < 8:
                    embs.append(embedding)
            return best_match
        return None

    @classmethod
    def register_captured_person(
        cls,
        embedding: np.ndarray,
        sample_image: Optional[str] = None,
        name: Optional[str] = None,
        threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """Registers a newly snapshotted person's face embedding into the registry."""
        match = cls.find_matching_captured_person(embedding, threshold=threshold)
        if match:
            embs = match.setdefault("embeddings", [])
            if len(embs) < 8:
                embs.append(embedding)
            return match

        person_entry = {
            "person_id": cls._next_person_id,
            "embedding": embedding,
            "embeddings": [embedding],
            "captured_at": datetime.now(timezone.utc),
            "sample_image": sample_image,
            "name": name or f"Person {cls._next_person_id}"
        }
        cls._next_person_id += 1
        cls._captured_persons.append(person_entry)
        logger.info(f"Registered new snapshotted person #{person_entry['person_id']} (Total: {len(cls._captured_persons)})")
        return person_entry

    @classmethod
    def crop_face_snapshot(
        cls,
        image: Any,
        face_box: Optional[Dict[str, int]] = None,
        max_dimension: int = 320,
        quality: int = 80
    ) -> Optional[str]:
        """
        Crops individual face region with comfortable head-and-shoulders margin padding (~30%)
        and compresses to lightweight base64 JPEG data URL for database storage.
        """
        if not image:
            return None

        try:
            if isinstance(image, str):
                cv_img = FaceService.decode_base64_image(image)
                pil_img = FaceService._to_pil_rgb(cv_img)
            else:
                pil_img = FaceService._to_pil_rgb(image)

            w_img, h_img = pil_img.size

            if face_box and "x" in face_box and "w" in face_box:
                x, y, w, h = face_box["x"], face_box["y"], face_box["w"], face_box["h"]
                cx = x + w / 2.0
                cy = y + h / 2.0
                side = max(w, h) * 1.35
                x1 = max(0, int(cx - side / 2.0))
                y1 = max(0, int(cy - side / 2.0))
                x2 = min(w_img, int(cx + side / 2.0))
                y2 = min(h_img, int(cy + side / 2.0))
                cropped = pil_img.crop((x1, y1, x2, y2))
            else:
                cropped = pil_img

            width, height = cropped.size
            if max(width, height) > max_dimension:
                scale = max_dimension / float(max(width, height))
                new_size = (int(width * scale), int(height * scale))
                cropped = cropped.resize(new_size, Image.Resampling.LANCZOS)

            buffer = io.BytesIO()
            cropped.save(buffer, format="JPEG", quality=quality, optimize=True)
            encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
            return f"data:image/jpeg;base64,{encoded}"
        except Exception as e:
            logger.warning(f"Failed to crop face snapshot: {e}")
            return cls.process_captured_image(image, max_dimension=max_dimension, quality=quality) if isinstance(image, str) else None

    @classmethod
    def _analyze_face_roi(cls, pil_img: Image.Image, face_box: Dict[str, Any], person_id: int = 1) -> Optional[Dict[str, Any]]:
        """Extracts Action Units and computes mood distribution for an individual face region."""
        w_img, h_img = pil_img.size
        x, y, w, h = face_box["x"], face_box["y"], face_box["w"], face_box["h"]

        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(w_img, x + w)
        y2 = min(h_img, y + h)

        if x2 - x1 < 20 or y2 - y1 < 20:
            return None

        # Canonical face ROI (128x128 for action unit analysis)
        face_roi = pil_img.crop((x1, y1, x2, y2)).resize((128, 128), Image.Resampling.BILINEAR)
        arr = np.array(face_roi, dtype=np.float32)
        gray = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]

        # Action Unit Spatial Slices
        mid_brow = gray[12:35, 52:76]
        brow_furrow = float(np.var(np.diff(mid_brow, axis=1))) if mid_brow.size > 0 else 0.0

        left_eye = gray[36:58, 20:56]
        right_eye = gray[36:58, 72:108]
        eye_contrast = float(np.std(left_eye) + np.std(right_eye)) / 2.0
        eye_darkness = float(255.0 - (np.mean(left_eye) + np.mean(right_eye)) / 2.0)

        cheeks = gray[58:82, 18:110]
        cheek_luminance = float(np.mean(cheeks))

        mouth_roi = gray[84:122, 28:100]
        m_h, m_w = mouth_roi.shape
        mouth_corners = float(np.mean(mouth_roi[:, :m_w // 4]) + np.mean(mouth_roi[:, 3 * m_w // 4:])) / 2.0
        mouth_center = float(np.mean(mouth_roi[:, m_w // 4: 3 * m_w // 4]))
        mouth_top = float(np.mean(mouth_roi[:m_h // 2, :]))
        mouth_bot = float(np.mean(mouth_roi[m_h // 2:, :]))
        mouth_open_var = float(np.var(mouth_roi))

        smile_score = (mouth_corners - mouth_center) + (mouth_top - mouth_bot) * 0.4

        # Affective Logit Computations
        l_neutral = 1.0
        l_happy = -0.5 + max(0.0, smile_score * 0.55) + max(0.0, (cheek_luminance - 110.0) * 0.03) - max(0.0, (brow_furrow - 15.0) * 0.08)
        l_calm = 0.8 - max(0.0, abs(smile_score - 1.0) * 0.2) - max(0.0, (brow_furrow - 10.0) * 0.1)
        l_focused = 0.5 + min(2.0, brow_furrow * 0.04) + min(1.5, eye_contrast * 0.03) - max(0.0, abs(smile_score) * 0.2)
        l_surprised = -1.5 + max(0.0, (mouth_open_var - 280.0) * 0.008) + max(0.0, (eye_contrast - 45.0) * 0.08)
        l_fatigued = -0.8 + max(0.0, (30.0 - eye_contrast) * 0.12) - max(0.0, smile_score * 0.4)
        l_stressed = -1.2 + max(0.0, (brow_furrow - 20.0) * 0.09) + max(0.0, (-smile_score) * 0.4)

        raw_logits = np.array([l_happy, l_calm, l_focused, l_neutral, l_surprised, l_fatigued, l_stressed], dtype=np.float32)

        # Temperature-scaled Softmax
        temperature = 0.85
        exp_logits = np.exp((raw_logits - np.max(raw_logits)) / temperature)
        probs = exp_logits / np.sum(exp_logits)

        emotion_keys = ["happy", "calm", "focused", "neutral", "surprised", "fatigued", "stressed"]
        breakdown = {k: round(float(probs[i] * 100.0), 1) for i, k in enumerate(emotion_keys)}

        dom_idx = int(np.argmax(probs))
        dominant_key = emotion_keys[dom_idx]
        profile = cls.EMOTION_PROFILES[dominant_key]

        valence = sum(probs[i] * cls.EMOTION_PROFILES[k]["valence"] for i, k in enumerate(emotion_keys))
        arousal = sum(probs[i] * cls.EMOTION_PROFILES[k]["arousal"] for i, k in enumerate(emotion_keys))
        confidence = round(float(probs[dom_idx] * 100.0), 1)

        # Biometric Face Recognition for 1-time snapshot de-duplication
        face_bounding = {"x": x1, "y": y1, "w": x2 - x1, "h": y2 - y1}
        emb = FaceService.extract_embedding(pil_img, face_bounding)
        matched = cls.find_matching_captured_person(emb)

        is_new_person = matched is None
        needs_snapshot = is_new_person
        matched_id = matched["person_id"] if matched else None
        person_name = matched.get("name") if matched else f"Person {person_id}"
        snapshot_status = "new_person" if is_new_person else "verified_same"

        return {
            "person_id": matched_id if matched_id else person_id,
            "face_box": face_bounding,
            "dominant_mood": dominant_key,
            "label": profile["label"],
            "emoji": profile["emoji"],
            "feeling_tag": profile["tag"],
            "color": profile["color"],
            "confidence": confidence,
            "valence": round(float(valence), 2),
            "arousal": round(float(arousal), 2),
            "breakdown": breakdown,
            "wellness_tip": profile["tip"],
            "is_new_person": is_new_person,
            "needs_snapshot": needs_snapshot,
            "matched_person_id": matched_id,
            "person_name": person_name,
            "snapshot_status": snapshot_status
        }

    @classmethod
    def analyze_face_mood(cls, image: Any, face_box: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """
        Processes camera image frame to detect all faces and quantify facial emotions simultaneously.
        Returns live telemetry for all detected people plus overall group affect metrics.
        """
        pil_img = FaceService._to_pil_rgb(image)

        # 1. Detect all faces in frame if bounding box not explicitly provided
        if face_box is not None:
            boxes = [face_box]
        else:
            boxes = FaceService.detect_faces(pil_img)

        if not boxes:
            return {
                "face_detected": False,
                "face_count": 0,
                "faces": [],
                "has_new_person": False,
                "needs_snapshot": False,
                "total_captured_persons": len(cls._captured_persons),
                "message": "No face detected in camera view. Please look at the camera.",
                "dominant_mood": "neutral",
                "feeling_tag": "Awaiting Face...",
                "emoji": "👤",
                "confidence": 0.0,
                "valence": 0.0,
                "arousal": 0.0,
                "breakdown": {k: 0.0 for k in cls.EMOTION_PROFILES},
                "wellness_tip": "Position yourself in front of the camera to begin live mood tracking.",
                "face_box": None,
                "group_summary": "Awaiting Faces",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        # 2. Analyze each detected face region
        faces_list = []
        for idx, box in enumerate(boxes):
            face_result = cls._analyze_face_roi(pil_img, box, person_id=idx + 1)
            if face_result:
                faces_list.append(face_result)

        if not faces_list:
            return {
                "face_detected": False,
                "face_count": 0,
                "faces": [],
                "has_new_person": False,
                "needs_snapshot": False,
                "total_captured_persons": len(cls._captured_persons),
                "message": "Face bounding boxes too small for reliable analysis.",
                "dominant_mood": "neutral",
                "feeling_tag": "Move Closer",
                "emoji": "👤",
                "confidence": 0.0,
                "valence": 0.0,
                "arousal": 0.0,
                "breakdown": {k: 0.0 for k in cls.EMOTION_PROFILES},
                "wellness_tip": "Move closer to the camera.",
                "face_box": None,
                "group_summary": "Move Closer",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        # Sort faces by area (width * height) so the most prominent person is person 1
        faces_list.sort(key=lambda f: f["face_box"]["w"] * f["face_box"]["h"], reverse=True)
        for i, f in enumerate(faces_list):
            if not f.get("matched_person_id"):
                f["person_id"] = i + 1

        primary = faces_list[0]
        face_count = len(faces_list)
        avg_valence = round(float(np.mean([f["valence"] for f in faces_list])), 2)
        avg_arousal = round(float(np.mean([f["arousal"] for f in faces_list])), 2)

        has_new_person = any(f.get("is_new_person", False) for f in faces_list)
        needs_snapshot = any(f.get("needs_snapshot", False) for f in faces_list)

        if face_count > 1:
            group_summary = f"{face_count} Persons Tracked: " + ", ".join(
                [f"P{f['person_id']} {f['emoji']} ({f['label'].split('/')[0].strip()})" for f in faces_list[:3]]
            )
        else:
            group_summary = primary["feeling_tag"]

        return {
            "face_detected": True,
            "face_count": face_count,
            "faces": faces_list,
            "face_box": primary["face_box"],
            "dominant_mood": primary["dominant_mood"],
            "label": primary["label"],
            "emoji": primary["emoji"],
            "feeling_tag": primary["feeling_tag"],
            "color": primary["color"],
            "confidence": primary["confidence"],
            "valence": primary["valence"],
            "arousal": primary["arousal"],
            "breakdown": primary["breakdown"],
            "wellness_tip": primary["wellness_tip"],
            "avg_valence": avg_valence,
            "avg_arousal": avg_arousal,
            "group_summary": group_summary,
            "has_new_person": has_new_person,
            "needs_snapshot": needs_snapshot,
            "person_id": primary["person_id"],
            "person_name": primary.get("person_name"),
            "is_new_person": primary.get("is_new_person", False),
            "total_captured_persons": len(cls._captured_persons),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    @classmethod
    def process_captured_image(cls, raw_image: Optional[str], max_dimension: int = 360, quality: int = 80) -> Optional[str]:
        """
        Processes and compresses captured face snapshot for efficient database storage.
        Converts to standardized base64 JPEG data URL format.
        """
        if not raw_image:
            return None

        try:
            # Strip base64 data URL header if present
            if "base64," in raw_image:
                base64_str = raw_image.split("base64,", 1)[1]
            else:
                base64_str = raw_image

            img_bytes = base64.b64decode(base64_str)
            img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

            # Downsample if larger than max_dimension to keep DB footprint minimal
            width, height = img.size
            if max(width, height) > max_dimension:
                scale = max_dimension / float(max(width, height))
                new_size = (int(width * scale), int(height * scale))
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            # Compress to JPEG in memory
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=quality, optimize=True)
            encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
            return f"data:image/jpeg;base64,{encoded}"
        except Exception as e:
            logger.warning(f"Could not compress mood image: {e}")
            if raw_image.startswith("data:image"):
                return raw_image
            return f"data:image/jpeg;base64,{raw_image}"

    @classmethod
    def log_mood(
        cls,
        user_id: Optional[int],
        mood_data: Dict[str, Any],
        note: Optional[str] = None,
        context: str = "camera_tracker",
        captured_image: Optional[str] = None,
        face_box: Optional[Dict[str, int]] = None
    ) -> MoodLog:
        """Saves a mood check-in snapshot with captured picture to the database."""
        dom_mood = mood_data.get("dominant_mood", "neutral")
        profile = cls.EMOTION_PROFILES.get(dom_mood, cls.EMOTION_PROFILES["neutral"])

        # Also support passing image directly inside mood_data dictionary
        if captured_image is None:
            captured_image = mood_data.get("image") or mood_data.get("captured_image")

        if face_box is None:
            face_box = mood_data.get("face_box")

        processed_img = None
        if captured_image:
            # Store full camera frame snapshot (not only cropped face)
            processed_img = cls.process_captured_image(captured_image, max_dimension=720, quality=82)

            # Register this person's face embedding into snapshotted registry
            try:
                cv_img = FaceService.decode_base64_image(captured_image)
                emb = FaceService.extract_embedding(cv_img, face_box=face_box)
                cls.register_captured_person(emb, sample_image=processed_img)
            except Exception as ex:
                logger.warning(f"Could not register captured person embedding: {ex}")

        log_entry = MoodLog(
            user_id=user_id,
            dominant_mood=dom_mood,
            feeling_tag=mood_data.get("feeling_tag", profile["tag"]),
            emoji=mood_data.get("emoji", profile["emoji"]),
            confidence=mood_data.get("confidence", 85.0),
            valence=mood_data.get("valence", 0.0),
            arousal=mood_data.get("arousal", 0.5),
            breakdown_json=json.dumps(mood_data.get("breakdown", {})),
            context=context,
            note=note.strip() if note else None,
            captured_image=processed_img,
            timestamp=datetime.now(timezone.utc)
        )
        db.session.add(log_entry)
        db.session.commit()
        return log_entry

    @classmethod
    def get_mood_analytics(cls, user_id: Optional[int] = None, days: int = 7) -> Dict[str, Any]:
        """
        Aggregates mood analytics over the last N days.
        Returns total check-ins, mood distribution counts, average sentiment index,
        and chronological day-by-day feeling trends for Chart.js.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        query = MoodLog.query.filter(MoodLog.timestamp >= cutoff)
        if user_id:
            query = query.filter(MoodLog.user_id == user_id)

        logs = query.order_by(MoodLog.timestamp.asc()).all()

        total_logs = len(logs)
        distribution = {k: 0 for k in cls.EMOTION_PROFILES}
        valence_scores = []
        arousal_scores = []

        timeline_labels = []
        timeline_valence = []
        timeline_arousal = []

        for log in logs:
            if log.dominant_mood in distribution:
                distribution[log.dominant_mood] += 1
            valence_scores.append(log.valence)
            arousal_scores.append(log.arousal)
            timeline_labels.append(log.timestamp.strftime("%a %I:%M%p"))
            timeline_valence.append(round(log.valence, 2))
            timeline_arousal.append(round(log.arousal, 2))

        avg_valence = round(float(np.mean(valence_scores)), 2) if valence_scores else 0.15
        avg_arousal = round(float(np.mean(arousal_scores)), 2) if arousal_scores else 0.45

        # Sentiment wellness index: mapped from valence [-1, 1] to [0%, 100%]
        wellness_index = round(float((avg_valence + 1.0) / 2.0 * 100.0), 1)

        # Most frequent mood
        top_mood = max(distribution, key=distribution.get) if total_logs > 0 else "neutral"

        return {
            "total_checkins": total_logs,
            "wellness_index": wellness_index,
            "avg_valence": avg_valence,
            "avg_arousal": avg_arousal,
            "dominant_mood": top_mood,
            "dominant_emoji": cls.EMOTION_PROFILES.get(top_mood, {}).get("emoji", "😊"),
            "distribution": distribution,
            "timeline": {
                "labels": timeline_labels[-20:],  # last 20 check-ins
                "valence": timeline_valence[-20:],
                "arousal": timeline_arousal[-20:]
            },
            "recent_logs": [l.to_dict() for l in logs[-10:]]
        }
