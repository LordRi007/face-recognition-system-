import json
import base64
from typing import List, Optional
import numpy as np
from cryptography.fernet import Fernet
from flask import current_app, request
from app.extensions import db
from app.models.audit_log import AuditLog
from app.models.user import User


class SecurityService:
    """Handles biometric encryption, cryptographic security, and audit logging."""

    @staticmethod
    def get_cipher() -> Fernet:
        """Returns a configured Fernet cipher instance using BIOMETRIC_ENCRYPTION_KEY."""
        key = current_app.config.get("BIOMETRIC_ENCRYPTION_KEY")
        if not key:
            raise ValueError("BIOMETRIC_ENCRYPTION_KEY is not configured in settings.")
        
        # Ensure key is bytes
        if isinstance(key, str):
            key_bytes = key.encode("utf-8")
        else:
            key_bytes = key
        
        return Fernet(key_bytes)

    @classmethod
    def encrypt_embedding(cls, embedding: List[float] | np.ndarray) -> str:
        """
        Serializes and AES-encrypts a facial embedding vector.
        Returns a URL-safe base64 string representation.
        """
        if isinstance(embedding, np.ndarray):
            embedding_list = embedding.tolist()
        else:
            embedding_list = list(embedding)

        json_bytes = json.dumps(embedding_list).encode("utf-8")
        cipher = cls.get_cipher()
        encrypted_bytes = cipher.encrypt(json_bytes)
        return encrypted_bytes.decode("utf-8")

    @classmethod
    def decrypt_embedding(cls, encrypted_str: str) -> np.ndarray:
        """
        Decrypts and deserializes an encrypted facial embedding back into a numpy array.
        """
        if not encrypted_str:
            raise ValueError("No encrypted embedding data provided.")
        
        cipher = cls.get_cipher()
        decrypted_bytes = cipher.decrypt(encrypted_str.encode("utf-8"))
        embedding_list = json.loads(decrypted_bytes.decode("utf-8"))
        return np.array(embedding_list, dtype=np.float32)

    @staticmethod
    def get_client_ip() -> str:
        """Extracts the client's real IP address considering proxy headers."""
        if request:
            if request.headers.get("X-Forwarded-For"):
                # Handle comma-separated list of proxies
                return request.headers.get("X-Forwarded-For").split(",")[0].strip()
            elif request.headers.get("X-Real-IP"):
                return request.headers.get("X-Real-IP").strip()
            return request.remote_addr or "127.0.0.1"
        return "127.0.0.1"

    @classmethod
    def log_event(
        cls,
        action: str,
        target_type: str,
        target_id: Optional[str | int] = None,
        actor_id: Optional[int] = None,
        details: Optional[str] = None
    ) -> AuditLog:
        """Records an immutable audit log entry for administrative & security actions."""
        ip = cls.get_client_ip()
        return AuditLog.log(
            action=action,
            target_type=target_type,
            target_id=target_id,
            actor_id=actor_id,
            details=details,
            ip_address=ip
        )
