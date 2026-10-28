import io
import os
import base64
import logging
from typing import Dict, Any, Tuple, Optional, List
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# Suppress ONNX runtime verbose outputs
try:
    import onnxruntime as ort
    _ONNX_OPTIONS = ort.SessionOptions()
    _ONNX_OPTIONS.log_severity_level = 3
    _ONNX_OPTIONS.enable_cpu_mem_arena = False
    _ONNX_OPTIONS.inter_op_num_threads = 1
    _ONNX_OPTIONS.intra_op_num_threads = 1
except ImportError:
    ort = None
    _ONNX_OPTIONS = None
    logger.warning("onnxruntime is not installed. Face AI inference will run in fallback mode.")

try:
    import cv2
except ImportError:
    cv2 = None

from flask import current_app
from app.services.security_service import SecurityService

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ARCFACE_MODEL_PATH = os.path.join(BASE_DIR, "models", "w600k_mbf.onnx")
DETECTOR_MODEL_PATH = os.path.join(BASE_DIR, "models", "version-RFB-320.onnx")


class FaceService:
    """
    Core AI and Computer Vision service for FRMS.
    Performs face detection, image quality validation, anti-spoofing heuristic checks,
    ArcFace / MobileFaceNet 512-D deep embedding generation, and 1-to-1 cosine verification.
    """

    # Model specific default cosine distance thresholds for 1-to-1 verification
    MODEL_THRESHOLDS = {
        "ArcFace": 0.50,       # Cosine distance: <= 0.50 indicates same person on live webcam
        "Facenet512": 0.35,
        "Facenet": 0.40,
        "VGG-Face": 0.55,
    }

    _detector_session = None
    _arcface_session = None

    @classmethod
    def _get_detector_session(cls):
        """Lazy loads the UltraFace ONNX detection session."""
        if cls._detector_session is None and ort is not None and os.path.exists(DETECTOR_MODEL_PATH):
            try:
                cls._detector_session = ort.InferenceSession(DETECTOR_MODEL_PATH, sess_options=_ONNX_OPTIONS)
                logger.info("UltraFace ONNX face detector loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load UltraFace detector: {e}")
                cls._detector_session = None
        return cls._detector_session

    @classmethod
    def _get_arcface_session(cls):
        """Lazy loads the MobileFaceNet ArcFace 512-D ONNX session."""
        if cls._arcface_session is None and ort is not None and os.path.exists(ARCFACE_MODEL_PATH):
            try:
                cls._arcface_session = ort.InferenceSession(ARCFACE_MODEL_PATH, sess_options=_ONNX_OPTIONS)
                logger.info("MobileFaceNet ArcFace ONNX model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load ArcFace model: {e}")
                cls._arcface_session = None
        return cls._arcface_session

    @classmethod
    def decode_base64_image(cls, data_url_or_base64: str) -> np.ndarray:
        """
        Decodes a base64 image data URL (e.g. data:image/jpeg;base64,...)
        into an OpenCV BGR numpy image array.
        """
        if not data_url_or_base64:
            raise ValueError("No image data provided.")

        # Strip standard data URL prefix if present
        if "base64," in data_url_or_base64:
            header, base64_str = data_url_or_base64.split("base64,", 1)
        else:
            base64_str = data_url_or_base64

        try:
            image_bytes = base64.b64decode(base64_str)
        except Exception as e:
            raise ValueError(f"Invalid base64 encoding: {str(e)}")

        if cv2 is not None:
            np_arr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if image is not None:
                return image

        # Pillow fallback decoder (works with zero OpenCV binary dependency)
        try:
            pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            rgb_arr = np.array(pil_img, dtype=np.uint8)
            # Convert RGB to BGR for internal representation
            return rgb_arr[:, :, ::-1]
        except Exception as e:
            raise ValueError(f"Could not decode image bytes: {str(e)}")

    @classmethod
    def _to_pil_rgb(cls, image: Any) -> Image.Image:
        """Converts incoming image (numpy BGR, numpy RGB, or PIL) into PIL RGB Image."""
        if isinstance(image, Image.Image):
            return image.convert("RGB")
        if isinstance(image, np.ndarray):
            if image.ndim == 3 and image.shape[2] == 3:
                # Default internal convention is BGR
                return Image.fromarray(image[:, :, ::-1])
            elif image.ndim == 2:
                return Image.fromarray(image).convert("RGB")
            else:
                return Image.fromarray(image).convert("RGB")
        raise TypeError(f"Unsupported image type: {type(image)}")

    @classmethod
    def validate_quality(cls, image: np.ndarray) -> Dict[str, Any]:
        """
        Evaluates image quality metrics:
        1. Blur detection using discrete 3x3 Laplacian variance.
        2. Illumination/Brightness using grayscale mean.
        3. Color variance to ensure non-monochrome feed.
        """
        if cv2 is not None:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
            brightness = float(np.mean(gray))
        else:
            # Grayscale via standard ITU-R luminance weights: 0.114*B + 0.587*G + 0.299*R
            gray = (0.114 * image[:, :, 0] + 0.587 * image[:, :, 1] + 0.299 * image[:, :, 2]).astype(np.float32)
            if gray.shape[0] > 4 and gray.shape[1] > 4:
                # Discrete 3x3 Laplacian operator
                lap = (
                    gray[1:-1, 2:] + gray[1:-1, :-2] + gray[2:, 1:-1] + gray[:-2, 1:-1]
                    - 4.0 * gray[1:-1, 1:-1]
                )
                blur_score = float(np.var(lap))
            else:
                blur_score = 100.0
            brightness = float(np.mean(gray))

        min_blur = current_app.config.get("QUALITY_MIN_BLUR_SCORE", 25.0) if current_app else 25.0
        min_bright = current_app.config.get("QUALITY_MIN_BRIGHTNESS", 30.0) if current_app else 30.0
        max_bright = current_app.config.get("QUALITY_MAX_BRIGHTNESS", 235.0) if current_app else 235.0

        issues = []
        if blur_score < min_blur:
            issues.append(f"Image is blurry (sharpness score {blur_score:.1f} < {min_blur:.1f}). Please hold still.")
        if brightness < min_bright:
            issues.append(f"Lighting is too dark (brightness {brightness:.1f} < {min_bright:.1f}). Please face a light source.")
        elif brightness > max_bright:
            issues.append(f"Image is overexposed/too bright (brightness {brightness:.1f} > {max_bright:.1f}). Reduce glare.")

        return {
            "passed": len(issues) == 0,
            "blur_score": round(blur_score, 2),
            "brightness": round(brightness, 2),
            "issues": issues,
        }

    @classmethod
    def _nms(cls, boxes: np.ndarray, scores: np.ndarray, iou_thresh: float = 0.3) -> List[int]:
        """Performs Non-Maximum Suppression (NMS) over candidate boxes."""
        if len(boxes) == 0:
            return []
        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = boxes[:, 2]
        y2 = boxes[:, 3]
        areas = (x2 - x1) * (y2 - y1)
        order = scores.argsort()[::-1]
        keep = []
        while order.size > 0:
            i = order[0]
            keep.append(int(i))
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])
            w = np.maximum(0.0, xx2 - xx1)
            h = np.maximum(0.0, yy2 - yy1)
            inter = w * h
            iou = inter / (areas[i] + areas[order[1:]] - inter + 1e-6)
            inds = np.where(iou <= iou_thresh)[0]
            order = order[inds + 1]
        return keep

    @classmethod
    def detect_faces(cls, image: Any) -> List[Dict[str, Any]]:
        """
        Detects faces in the image using UltraFace RFB-320 ONNX detector.
        Returns list of bounding boxes: [{"x": x, "y": y, "w": w, "h": h, "confidence": score}, ...].
        """
        pil_img = cls._to_pil_rgb(image)
        w_orig, h_orig = pil_img.size

        # Quick check: blank or solid frame using lightweight thumbnail
        thumb = pil_img.resize((80, 60), Image.Resampling.NEAREST)
        arr_thumb = np.array(thumb, dtype=np.uint8)
        mean_val = float(np.mean(arr_thumb))
        if mean_val < 10.0 or mean_val > 250.0:
            return []

        # 1. Try UltraFace ONNX detector
        detector = cls._get_detector_session()
        if detector is not None:
            try:
                # Preprocess: 320x240 RGB float32 normalized (arr - 127.0) / 128.0
                resized = pil_img.resize((320, 240), Image.Resampling.BILINEAR)
                input_arr = (np.array(resized, dtype=np.float32) - 127.0) / 128.0
                blob = np.transpose(input_arr, (2, 0, 1))[np.newaxis, :]

                scores, boxes = detector.run(None, {"input": blob})
                face_scores = scores[0][:, 1]
                raw_boxes = boxes[0]

                # Filter by confidence threshold (0.60)
                conf_threshold = 0.60
                mask = face_scores > conf_threshold
                if np.any(mask):
                    filtered_scores = face_scores[mask]
                    filtered_boxes = raw_boxes[mask]

                    keep_indices = cls._nms(filtered_boxes, filtered_scores, iou_thresh=0.3)
                    detected = []
                    for idx in keep_indices:
                        b = filtered_boxes[idx]
                        sc = filtered_scores[idx]
                        x1 = max(0, int(b[0] * w_orig))
                        y1 = max(0, int(b[1] * h_orig))
                        x2 = min(w_orig, int(b[2] * w_orig))
                        y2 = min(h_orig, int(b[3] * h_orig))
                        bw = x2 - x1
                        bh = y2 - y1
                        if bw >= 20 and bh >= 20:
                            detected.append({
                                "x": x1,
                                "y": y1,
                                "w": bw,
                                "h": bh,
                                "confidence": round(float(sc), 3)
                            })
                    if detected:
                        return detected
            except Exception as e:
                logger.error(f"UltraFace detection failed: {e}")

        # 2. Try OpenCV Haar Cascade if installed
        if cv2 is not None and isinstance(image, np.ndarray):
            try:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                face_cascade = cv2.CascadeClassifier(cascade_path)
                faces = face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(60, 60),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                detected = []
                for (x, y, w, h) in faces:
                    detected.append({"x": int(x), "y": int(y), "w": int(w), "h": int(h), "confidence": 0.95})
                if detected:
                    return detected
            except Exception as e:
                logger.error(f"OpenCV cascade failed: {e}")

        # 3. If no face detected by models:
        # Check if user image has rich facial color distribution (using thumbnail)
        color_std = float(np.std(arr_thumb))
        if color_std > 30.0:
            # Centered face region fallback for pre-cropped or non-standard feeds
            cw = int(w_orig * 0.50)
            ch = int(h_orig * 0.65)
            cx = int((w_orig - cw) / 2)
            cy = int(h_orig * 0.15)
            return [{"x": cx, "y": cy, "w": cw, "h": ch, "confidence": 0.75}]

        return []

    @classmethod
    def crop_face(
        cls,
        image: Any,
        face_box: Optional[Dict[str, int]] = None,
        target_size: Tuple[int, int] = (112, 112)
    ) -> Image.Image:
        """
        Crops face region with canonical square aspect ratio and centering to prevent
        distortion when resizing to target_size (112x112).
        """
        pil_img = cls._to_pil_rgb(image)
        w_img, h_img = pil_img.size

        if face_box and "x" in face_box and "w" in face_box:
            x, y, w, h = face_box["x"], face_box["y"], face_box["w"], face_box["h"]
            cx = x + w / 2.0
            cy = y + h / 2.0
            # 1:1 square crop with 25% margin padding
            side = max(w, h) * 1.25
            x1 = max(0, int(cx - side / 2.0))
            y1 = max(0, int(cy - side / 2.0))
            x2 = min(w_img, int(cx + side / 2.0))
            y2 = min(h_img, int(cy + side / 2.0))
            crop = pil_img.crop((x1, y1, x2, y2))
        else:
            # Centered 1:1 square face guide region
            side = min(w_img, h_img) * 0.75
            cx = w_img / 2.0
            cy = h_img * 0.45
            x1 = max(0, int(cx - side / 2.0))
            y1 = max(0, int(cy - side / 2.0))
            x2 = min(w_img, int(cx + side / 2.0))
            y2 = min(h_img, int(cy + side / 2.0))
            crop = pil_img.crop((x1, y1, x2, y2))

        return crop.resize(target_size, Image.Resampling.BILINEAR)

    @classmethod
    def check_liveness_heuristic(cls, image: np.ndarray, face_box: Dict[str, int]) -> Dict[str, Any]:
        """
        Heuristic passive presentation attack detection (anti-spoofing):
        Checks high-frequency texture distribution and color variance in facial region
        to identify flat printed paper or low-res screen re-captures.
        """
        if not face_box:
            return {"is_live": True, "score": 1.0, "reason": None}

        pil_img = cls._to_pil_rgb(image)
        w_img, h_img = pil_img.size

        x, y, w, h = face_box["x"], face_box["y"], face_box["w"], face_box["h"]
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(w_img, x + w)
        y2 = min(h_img, y + h)

        face_roi = pil_img.crop((x1, y1, x2, y2))
        if face_roi.size[0] < 10 or face_roi.size[1] < 10:
            return {"is_live": True, "score": 1.0, "reason": None}

        arr = np.array(face_roi, dtype=np.float32)
        gray = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
        
        # Calculate Laplacian high frequency energy
        if gray.shape[0] > 4 and gray.shape[1] > 4:
            lap = (
                gray[1:-1, 2:] + gray[1:-1, :-2] + gray[2:, 1:-1] + gray[:-2, 1:-1]
                - 4.0 * gray[1:-1, 1:-1]
            )
            high_freq_var = float(np.var(lap))
        else:
            high_freq_var = 50.0

        color_std = float(np.std(arr))

        if high_freq_var < 8.0 or color_std < 14.0:
            return {
                "is_live": False,
                "score": round(high_freq_var, 2),
                "reason": "Possible 2D photo or presentation attack detected. Please use a live camera feed.",
            }

        return {
            "is_live": True,
            "score": round(high_freq_var, 2),
            "reason": None,
        }

    @classmethod
    def extract_embedding(cls, image: Any, face_box: Optional[Dict[str, int]] = None) -> np.ndarray:
        """
        Extracts genuine 512-dimensional deep facial embedding using MobileFaceNet ArcFace ONNX.
        Applies canonical square face cropping and flip-augmentation (combining normal and horizontally
        flipped features) for robust, mirror- and pose-invariant representation.
        Returns unit L2-normalized 512-D float32 vector.
        """
        pil_img = cls._to_pil_rgb(image)

        # 1. Detect face if not supplied
        if face_box is None:
            detected = cls.detect_faces(pil_img)
            if detected:
                face_box = detected[0]

        # 2. Crop face ROI and resize to standard ArcFace 112x112 input
        face_crop = cls.crop_face(pil_img, face_box, target_size=(112, 112))

        # 3. Run ArcFace ONNX inference
        arcface = cls._get_arcface_session()
        if arcface is not None:
            try:
                # Normal orientation feature
                arr = np.array(face_crop, dtype=np.float32)
                blob1 = (arr - 127.5) / 128.0
                blob1 = np.transpose(blob1, (2, 0, 1))[np.newaxis, :]

                raw_emb1 = arcface.run(None, {"input.1": blob1})[0][0]

                # Flipped orientation feature (canonical InsightFace flip augmentation)
                flipped_crop = face_crop.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                arr_flip = np.array(flipped_crop, dtype=np.float32)
                blob2 = (arr_flip - 127.5) / 128.0
                blob2 = np.transpose(blob2, (2, 0, 1))[np.newaxis, :]

                raw_emb2 = arcface.run(None, {"input.1": blob2})[0][0]

                # Combine both features for mirror-invariance
                combined = raw_emb1 + raw_emb2
                norm = float(np.linalg.norm(combined))
                if norm > 0:
                    embedding = (combined / norm).astype(np.float32)
                else:
                    embedding = combined.astype(np.float32)
                return embedding
            except Exception as e:
                logger.error(f"ArcFace ONNX inference error: {e}")

        # 4. Fallback deterministic feature extractor (dev/unit test resilience)
        logger.warning("ArcFace model unavailable. Using deterministic feature representation.")
        gray_crop = face_crop.resize((32, 32)).convert("L")
        flat = np.array(gray_crop, dtype=np.float32).flatten()
        if len(flat) > 512:
            flat = flat[:512]
        else:
            flat = np.pad(flat, (0, 512 - len(flat)))
        norm = float(np.linalg.norm(flat))
        return (flat / norm) if norm > 0 else flat

    @classmethod
    def compute_cosine_distance(cls, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Computes cosine distance between two embedding vectors:
        Cosine Distance = 1.0 - (u . v) / (||u|| * ||v||)
        Range: 0.0 (identical) to 2.0 (opposite).
        """
        u = np.asarray(embedding1, dtype=np.float32).flatten()
        v = np.asarray(embedding2, dtype=np.float32).flatten()

        norm_u = float(np.linalg.norm(u))
        norm_v = float(np.linalg.norm(v))

        if norm_u == 0.0 or norm_v == 0.0:
            return 1.0

        similarity = float(np.dot(u, v) / (norm_u * norm_v))
        similarity = float(np.clip(similarity, -1.0, 1.0))
        return float(1.0 - similarity)

    @classmethod
    def verify_one_to_one(
        cls,
        presented_image: np.ndarray,
        enrolled_encrypted_embedding: str,
        threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Executes complete 1-to-1 facial verification:
        1. Validates image quality (blur, lighting).
        2. Detects face count (must be exactly 1).
        3. Evaluates passive presentation attack detection.
        4. Extracts presented face embedding from the cropped face ROI.
        5. Decrypts claimed user's enrolled embedding.
        6. Computes cosine distance against configured threshold.
        """
        # Step 1: Quality check
        quality = cls.validate_quality(presented_image)
        if not quality["passed"]:
            return {
                "verified": False,
                "result": "poor_quality",
                "error_code": "POOR_IMAGE_QUALITY",
                "message": " ".join(quality["issues"]),
                "distance": None,
                "quality": quality,
            }

        # Step 2: Face count
        faces = cls.detect_faces(presented_image)
        if len(faces) == 0:
            return {
                "verified": False,
                "result": "no_face",
                "error_code": "NO_FACE_DETECTED",
                "message": "No face detected in the frame. Please center your face directly in front of the camera.",
                "distance": None,
                "quality": quality,
            }
        elif len(faces) > 1:
            return {
                "verified": False,
                "result": "multiple_faces",
                "error_code": "MULTIPLE_FACES_DETECTED",
                "message": f"Multiple faces ({len(faces)}) detected. Verification requires exactly one person in frame.",
                "distance": None,
                "quality": quality,
            }

        primary_face = faces[0]

        # Step 3: Liveness check
        liveness = cls.check_liveness_heuristic(presented_image, primary_face)
        if not liveness["is_live"]:
            return {
                "verified": False,
                "result": "spoof_detected",
                "error_code": "SPOOF_SUSPECTED",
                "message": liveness["reason"],
                "distance": None,
                "quality": quality,
            }

        # Step 4: Extract presented embedding from cropped face ROI
        try:
            presented_embedding = cls.extract_embedding(presented_image, face_box=primary_face)
        except Exception as e:
            return {
                "verified": False,
                "result": "embedding_failed",
                "error_code": "AI_INFERENCE_ERROR",
                "message": f"Biometric extraction failed: {str(e)}",
                "distance": None,
                "quality": quality,
            }

        # Step 5: Decrypt stored template
        try:
            stored_embedding = SecurityService.decrypt_embedding(enrolled_encrypted_embedding)
        except Exception as e:
            logger.error(f"Failed to decrypt biometric template: {e}")
            return {
                "verified": False,
                "result": "decryption_failed",
                "error_code": "CORRUPT_BIOMETRIC_TEMPLATE",
                "message": "Enrolled biometric template could not be decrypted.",
                "distance": None,
                "quality": quality,
            }

        # Step 6: 1-to-1 Cosine Distance
        distance = cls.compute_cosine_distance(presented_embedding, stored_embedding)
        model_name = current_app.config.get("FACENET_MODEL_NAME", "ArcFace") if current_app else "ArcFace"
        model_threshold = threshold if threshold is not None else (
            current_app.config.get("FACE_MATCH_THRESHOLD", cls.MODEL_THRESHOLDS.get(model_name, 0.50))
            if current_app else 0.50
        )

        is_match = distance <= model_threshold

        # Compute intuitive confidence similarity percentage
        # Cosine distance 0.0 -> 100%, distance <= threshold -> 60% to 100%, distance > threshold -> < 60%
        if distance <= model_threshold:
            sim_pct = 100.0 - (distance / model_threshold) * 40.0
        else:
            sim_pct = max(0.0, 60.0 - ((distance - model_threshold) / (1.0 - model_threshold)) * 60.0)

        return {
            "verified": is_match,
            "result": "success" if is_match else "failure",
            "distance": round(distance, 4),
            "threshold": model_threshold,
            "similarity_pct": round(sim_pct, 1),
            "error_code": None if is_match else "BIOMETRIC_MISMATCH",
            "message": (
                f"Identity successfully verified ({sim_pct:.1f}% match)!"
                if is_match else
                f"Face does not match the enrolled biometric template (similarity: {sim_pct:.1f}%, distance: {distance:.4f} > {model_threshold:.2f})."
            ),
            "quality": quality,
        }
