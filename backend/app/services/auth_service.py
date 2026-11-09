from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select

from app.core.errors import AppError
from app.core.security import (
    UserPrincipal,
    hash_password,
    hash_refresh_token,
    new_refresh_token,
    refresh_expiration,
    verify_password,
)
from app.core.settings import Settings
from app.db.database import Database
from app.db.models import RefreshTokenRecord, UserRecord


class AuthService:
    def __init__(self, database: Database, settings: Settings) -> None:
        self.database = database
        self.settings = settings

    def bootstrap(self) -> None:
        username = self.settings.auth_bootstrap_username
        password = self.settings.auth_bootstrap_password
        if not self.settings.auth_enabled or not username or not password:
            return
        with self.database.session() as session:
            existing = session.scalar(select(UserRecord).where(UserRecord.username == username))
            if existing is None:
                session.add(
                    UserRecord(
                        id=str(uuid4()),
                        username=username,
                        password_hash=hash_password(password),
                        role=self.settings.auth_bootstrap_role,
                        is_active=True,
                    )
                )

    def login(self, username: str, password: str) -> UserPrincipal:
        with self.database.session() as session:
            user = session.scalar(select(UserRecord).where(UserRecord.username == username))
            if user is None or not user.is_active or not verify_password(password, user.password_hash):
                raise AppError("unauthorized", "Credenciales inválidas.", 401)
            return UserPrincipal(user.id, user.username, user.role)

    def issue_refresh(self, user: UserPrincipal) -> tuple[str, datetime]:
        raw_token = new_refresh_token()
        expires_at = refresh_expiration(self.settings)
        with self.database.session() as session:
            session.add(
                RefreshTokenRecord(
                    id=str(uuid4()),
                    token_hash=hash_refresh_token(raw_token),
                    user_id=user.id,
                    created_at=datetime.now(UTC),
                    expires_at=expires_at,
                )
            )
        return raw_token, expires_at

    def rotate_refresh(self, raw_token: str) -> tuple[UserPrincipal, str, datetime]:
        token_hash = hash_refresh_token(raw_token)
        now = datetime.now(UTC)
        with self.database.session() as session:
            record = session.scalar(
                select(RefreshTokenRecord).where(RefreshTokenRecord.token_hash == token_hash)
            )
            expires_at = _as_utc(record.expires_at) if record is not None else now
            if record is None or record.revoked_at is not None or expires_at <= now:
                raise AppError("unauthorized", "Sesión inválida o expirada.", 401)
            user = session.get(UserRecord, record.user_id)
            if user is None or not user.is_active:
                raise AppError("unauthorized", "Sesión inválida o expirada.", 401)
            record.revoked_at = now
            principal = UserPrincipal(user.id, user.username, user.role)
            replacement = new_refresh_token()
            expires_at = refresh_expiration(self.settings)
            session.add(
                RefreshTokenRecord(
                    id=str(uuid4()),
                    token_hash=hash_refresh_token(replacement),
                    user_id=user.id,
                    created_at=now,
                    expires_at=expires_at,
                )
            )
            return principal, replacement, expires_at

    def revoke_refresh(self, raw_token: str) -> None:
        with self.database.session() as session:
            record = session.scalar(
                select(RefreshTokenRecord).where(
                    RefreshTokenRecord.token_hash == hash_refresh_token(raw_token)
                )
            )
            if record is not None and record.revoked_at is None:
                record.revoked_at = datetime.now(UTC)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
