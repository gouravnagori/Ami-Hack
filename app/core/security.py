from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import Role, settings

ph = PasswordHasher()


def hash_password(password: str) -> str:
    """Hash a plaintext password using Argon2id."""
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against an Argon2 hash."""
    try:
        return ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, Exception):
        return False


def create_token(
    user_id: str,
    role: Role,
    token_type: str = "access",
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a signed JWT token with user_id, role, type, and expiration."""
    now = datetime.now(UTC)
    if expires_delta:
        expire = now + expires_delta
    elif token_type == "refresh":
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": str(role),
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(
    user_id: str, role: Role, extra_claims: dict[str, Any] | None = None
) -> str:
    return create_token(
        user_id=user_id,
        role=role,
        token_type="access",
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        extra_claims=extra_claims,
    )


def create_refresh_token(user_id: str, role: Role) -> str:
    return create_token(
        user_id=user_id,
        role=role,
        token_type="refresh",
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def mask_phone(phone: str | None) -> str:
    """Mask phone number per Rule R7 (e.g. +91 98•••••21)."""
    if not phone:
        return ""
    clean = phone.strip()
    if len(clean) < 7:
        return "•••••••"
    prefix = clean[:5]
    suffix = clean[-2:]
    bullets = "•" * max(len(clean) - 7, 5)
    return f"{prefix}{bullets}{suffix}"


def generate_otp() -> str:
    """Generate a cryptographically secure 6-digit numeric OTP."""
    import secrets

    return f"{secrets.randbelow(900000) + 100000}"


def hash_otp(otp: str) -> str:
    """Hash an OTP using SHA-256."""
    import hashlib

    return hashlib.sha256(otp.strip().encode("utf-8")).hexdigest()


def verify_otp(plain_otp: str, hashed_otp: str) -> bool:
    """Verify an OTP with constant-time comparison."""
    import hmac

    return hmac.compare_digest(hash_otp(plain_otp), hashed_otp)
