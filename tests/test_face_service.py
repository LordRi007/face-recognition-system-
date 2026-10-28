import pytest
import numpy as np
from app.services.security_service import SecurityService
from app.services.face_service import FaceService
from app.models.face import FaceEnrollment
from app.extensions import db


def test_biometric_encryption_roundtrip(app, dummy_face_embedding):
    """Verify raw facial embeddings are correctly encrypted with AES and decrypted identically."""
    with app.app_context():
        encrypted_ciphertext = SecurityService.encrypt_embedding(dummy_face_embedding)
        assert isinstance(encrypted_ciphertext, str)
        assert len(encrypted_ciphertext) > 50

        decrypted_array = SecurityService.decrypt_embedding(encrypted_ciphertext)
        assert isinstance(decrypted_array, np.ndarray)
        assert decrypted_array.shape == (512,)
        # Vectors should match with high numerical precision
        np.testing.assert_allclose(dummy_face_embedding, decrypted_array, rtol=1e-5, atol=1e-5)


def test_cosine_distance_computation():
    """Verify cosine distance mathematics."""
    vec_a = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    vec_b = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    vec_c = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    vec_d = np.array([-1.0, 0.0, 0.0], dtype=np.float32)

    # Identical vectors: distance should be 0.0
    dist_same = FaceService.compute_cosine_distance(vec_a, vec_b)
    assert abs(dist_same - 0.0) < 1e-4

    # Orthogonal vectors: distance should be 1.0
    dist_ortho = FaceService.compute_cosine_distance(vec_a, vec_c)
    assert abs(dist_ortho - 1.0) < 1e-4

    # Opposite vectors: distance should be 2.0
    dist_opp = FaceService.compute_cosine_distance(vec_a, vec_d)
    assert abs(dist_opp - 2.0) < 1e-4


def test_quality_validation_dark_image(app):
    """Verify pitch black image fails brightness check."""
    with app.app_context():
        black_img = np.zeros((480, 640, 3), dtype=np.uint8)
        quality = FaceService.validate_quality(black_img)
        assert quality["passed"] is False
        assert any("dark" in iss.lower() for iss in quality["issues"])


def test_voluntary_biometric_deletion(client, seed_data, dummy_face_embedding):
    """Verify voluntary consent revocation wipes facial embeddings from database."""
    user = seed_data["user"]
    encrypted = SecurityService.encrypt_embedding(dummy_face_embedding)
    enrollment = FaceEnrollment(
        user_id=user.id,
        encrypted_embedding=encrypted,
        model_name="Facenet512",
        samples_count=1
    )
    db.session.add(enrollment)
    db.session.commit()

    assert user.has_face_enrolled is True

    # User logs in and deletes their own enrollment
    client.post("/login", data={"email": "user@test.local", "password": "UserPass123!"})
    res = client.post(f"/users/{user.id}/delete-face", follow_redirects=True)
    assert res.status_code == 200

    db.session.refresh(user)
    assert user.has_face_enrolled is False
    assert FaceEnrollment.query.filter_by(user_id=user.id).first() is None
