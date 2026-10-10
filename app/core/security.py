"""Argon2 pour les mots de passe + JWT access/refresh."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHash

from app.core.config import get_settings

_ph = PasswordHasher()


# ---------- Mots de passe ----------

def hash_password(plain: str) -> str:
    return _ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, plain)
    except (VerifyMismatchError, VerificationError, InvalidHash):
        return False


# ---------- JWT ----------

def _secret() -> str:
    return get_settings().jwt_secret


def _alg() -> str:
    return get_settings().jwt_algorithm


def create_access_token(user_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "typ": "access",
        "jti": uuid4().hex,
        "iat": int(now.timestamp()),
        "exp": int(
            (now + timedelta(minutes=get_settings().access_token_ttl_minutes)).timestamp()
        ),
    }
    return jwt.encode(payload, _secret(), algorithm=_alg())


def create_refresh_token(user_id: int) -> tuple[str, str, datetime]:
    """Retourne (token JWT, hash du token pour la base, expires_at)."""
    now = datetime.now(timezone.utc)
    jti = uuid4().hex
    expires_at = now + timedelta(days=get_settings().refresh_token_ttl_days)
    payload = {
        "sub": str(user_id),
        "typ": "refresh",
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, _secret(), algorithm=_alg())
    return token, _hash_token(token), expires_at


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def decode_token(token: str) -> dict:
    """Retourne le payload ou lève jwt.PyJWTError."""
    return jwt.decode(token, _secret(), algorithms=[_alg()])


def hash_refresh_token(token: str) -> str:
    """Expose le hash pour la couche service (recherche en base)."""
    return _hash_token(token)