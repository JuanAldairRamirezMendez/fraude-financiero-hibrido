from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.core.settings import get_settings


def test_alembic_upgrade_creates_schema(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    database_path = tmp_path / "migration.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    get_settings.cache_clear()
    config_path = Path(__file__).resolve().parents[2] / "alembic.ini"
    config = Config(str(config_path))
    command.upgrade(config, "head")

    engine = create_engine(f"sqlite:///{database_path}")
    tables = set(inspect(engine).get_table_names())
    assert {"decisions", "alerts", "audit_log", "idempotency_keys", "alembic_version"} <= tables
    engine.dispose()
    get_settings.cache_clear()
