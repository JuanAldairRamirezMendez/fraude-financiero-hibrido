from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = PROJECT_ROOT / "backend"
ARTIFACTS_DIR = BACKEND_ROOT / "artifacts"


class Settings(BaseSettings):
    """Application settings, loaded from environment variables and ``.env``."""

    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env", BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "SentinelAI Fraud API"
    app_version: str = "1.0.0"
    environment: str = Field(default="development", alias="APP_ENV")
    debug: bool = False
    api_prefix: str = "/api/v1"

    model_path: Path = PROJECT_ROOT / "models_saved" / "xgboost_tier2_isotonic.pkl"
    preprocessor_path: Path = ARTIFACTS_DIR / "preprocessor.joblib"
    feature_contract_path: Path = ARTIFACTS_DIR / "feature_contract.json"
    model_metadata_path: Path = ARTIFACTS_DIR / "model_metadata.json"
    snapshot_path: Path = ARTIFACTS_DIR / "overview_snapshot.json"
    transactions_path: Path = ARTIFACTS_DIR / "overview_transactions.parquet"
    static_dir: Path = PROJECT_ROOT / "frontend" / "dist"

    database_url: str = f"sqlite:///{ARTIFACTS_DIR / 'fraud.db'}"
    db_pool_size: int = 5
    db_max_overflow: int = 5
    fail_fast: bool = True
    enable_docs: bool = True
    seed_snapshot_alerts: bool = True

    cors_origins: tuple[str, ...] = ("http://localhost:8443", "http://127.0.0.1:8443")
    trusted_hosts: tuple[str, ...] = ("*",)
    rate_limit_analyze: str = "60/minute"
    rate_limit_read: str = "240/minute"
    idempotency_ttl_hours: int = 24
    request_timeout_seconds: int = 30
    log_level: str = "INFO"
    expose_prometheus: bool = True

    auth_enabled: bool = False
    jwt_secret_key: str = "development-only-change-me"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    auth_cookie_secure: bool = False
    auth_cookie_domain: str | None = None
    auth_cookie_samesite: str = "lax"
    auth_bootstrap_username: str | None = None
    auth_bootstrap_password: str | None = None
    auth_bootstrap_role: str = "analyst"

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        allowed = {"development", "test", "staging", "production"}
        normalized = value.lower()
        if normalized not in allowed:
            raise ValueError(f"environment must be one of {sorted(allowed)}")
        return normalized

    @model_validator(mode="after")
    def validate_auth(self) -> Settings:
        if self.auth_enabled and len(self.jwt_secret_key) < 32:
            raise ValueError("JWT_SECRET_KEY must contain at least 32 characters when auth is enabled")
        if self.access_token_minutes < 1 or self.refresh_token_days < 1:
            raise ValueError("Token lifetimes must be positive")
        if self.auth_cookie_samesite not in {"lax", "strict", "none"}:
            raise ValueError("AUTH_COOKIE_SAMESITE must be lax, strict or none")
        if self.auth_cookie_samesite == "none" and not self.auth_cookie_secure:
            raise ValueError("AUTH_COOKIE_SECURE must be true when SameSite is none")
        if self.is_production and self.auth_enabled and self.jwt_secret_key == "development-only-change-me":
            raise ValueError("JWT_SECRET_KEY must be configured in production")
        return self

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_test(self) -> bool:
        return self.environment == "test"


@lru_cache
def get_settings() -> Settings:
    return Settings()
