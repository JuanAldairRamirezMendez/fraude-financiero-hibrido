from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
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

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        allowed = {"development", "test", "staging", "production"}
        normalized = value.lower()
        if normalized not in allowed:
            raise ValueError(f"environment must be one of {sorted(allowed)}")
        return normalized

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_test(self) -> bool:
        return self.environment == "test"


@lru_cache
def get_settings() -> Settings:
    return Settings()
