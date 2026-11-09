from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from .models import Base


class Database:
    """Small SQLAlchemy wrapper with SQLite-friendly pool settings."""

    def __init__(self, url: str, *, pool_size: int = 5, max_overflow: int = 5) -> None:
        connect_args: dict[str, object] = {}
        engine_kwargs: dict[str, object] = {"pool_pre_ping": True, "future": True}
        if url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
            engine_kwargs.pop("pool_size", None)
            engine_kwargs["poolclass"] = None
        else:
            engine_kwargs.update(pool_size=pool_size, max_overflow=max_overflow)

        self.url = url
        self.engine = create_engine(url, connect_args=connect_args, **engine_kwargs)
        self._session_factory = sessionmaker(bind=self.engine, expire_on_commit=False, future=True)

        if url.startswith("sqlite"):
            @event.listens_for(self.engine, "connect")
            def _sqlite_pragmas(dbapi_connection, _connection_record):  # type: ignore[no-untyped-def]
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA busy_timeout=5000")
                cursor.close()

    def create_all(self) -> None:
        Base.metadata.create_all(self.engine)

    @contextmanager
    def session(self) -> Iterator[Session]:
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def ping(self) -> bool:
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def dispose(self) -> None:
        self.engine.dispose()
