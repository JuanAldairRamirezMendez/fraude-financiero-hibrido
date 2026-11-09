from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.errors import AppError
from app.core.settings import Settings

PASSWORD_HASHER = PasswordHasher()


@dataclass(frozen=True, slots=True)
class UserPrincipal:
    id: str
    username: str
    role: str


def hash_password(password: str) -> str:
    return PASSWORD_HASHER.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return PASSWORD_HASHER.verify(password_hash, password)
    except (InvalidHashError, VerificationError, VerifyMismatchError):
        return False


def new_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _encode_token(
    subject: UserPrincipal,
    token_type: str,
    expires_at: datetime,
    settings: Settings,
    jti: str | None = None,
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject.id,
        "username": subject.username,
        "role": subject.role,
        "type": token_type,
        "iat": now,
        "exp": expires_at,
    }
    if jti:
        payload["jti"] = jti
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(subject: UserPrincipal, settings: Settings) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_minutes)
    return _encode_token(subject, "access", expires_at, settings)


def decode_access_token(token: str, settings: Settings) -> UserPrincipal:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "username", "role", "type", "exp"]},
        )
    except jwt.PyJWTError as exc:
        raise AppError("unauthorized", "Credenciales inválidas.", 401) from exc
    if payload.get("type") != "access":
        raise AppError("unauthorized", "Credenciales inválidas.", 401)
    return UserPrincipal(
        id=str(payload["sub"]),
        username=str(payload["username"]),
        role=str(payload["role"]),
    )


def refresh_expiration(settings: Settings) -> datetime:
    return datetime.now(UTC) + timedelta(days=settings.refresh_token_days)


def csrf_token() -> str:
    return secrets.token_urlsafe(32)
