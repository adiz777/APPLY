import base64
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import bcrypt
import jwt
from cryptography.fernet import Fernet
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db


bearer_scheme = HTTPBearer(auto_error=False)


def _get_fernet() -> Fernet:
    if settings.apply_encryption_key:
        try:
            return Fernet(settings.apply_encryption_key.encode("utf-8"))
        except Exception:
            pass
    derived = base64.urlsafe_b64encode(hashlib.sha256(settings.apply_secret_key.encode("utf-8")).digest())
    return Fernet(derived)


def encrypt_secret(plain_text: str) -> str:
    if not plain_text:
        return ""
    return _get_fernet().encrypt(plain_text.encode("utf-8")).decode("utf-8")


def decrypt_secret(cipher_text: str) -> str:
    if not cipher_text:
        return ""
    try:
        return _get_fernet().decrypt(cipher_text.encode("utf-8")).decode("utf-8")
    except Exception:
        return ""


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(subject: str, expires_minutes: int = 60 * 24) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload = {"sub": subject, "exp": expire, "iat": datetime.now(timezone.utc)}
    return jwt.encode(payload, settings.apply_secret_key, algorithm="HS256")


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    try:
        return jwt.decode(token, settings.apply_secret_key, algorithms=["HS256"])
    except Exception:
        return None


def compute_approval_hash(
    job_id: int,
    cv_version_id: Optional[int],
    cover_letter_id: Optional[int],
    form_answers: dict[str, Any],
    work_eligibility_statement: str,
    sponsorship_Required: bool,
) -> str:
    import json

    canonical = json.dumps(
        {
            "job_id": job_id,
            "cv_version_id": cv_version_id,
            "cover_letter_id": cover_letter_id,
            "form_answers": form_answers or {},
            "work_eligibility_statement": (work_eligibility_statement or "").strip(),
            "sponsorship_required": bool(sponsorship_Required),
        },
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
