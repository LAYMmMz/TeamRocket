from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy.orm import Session

from app.core.db import (
    DATABASE_URL,
    SessionLocal,
    engine,
    get_db,
    get_shared_store,
    init_dev2_db,
    register_shared_runtime,
)
from app.models.dev2_models import Base


class _CompatDatabaseManager:
    """Backward-compatible wrapper delegating to app.core.db."""

    def __init__(self) -> None:
        self.sqlite_engine = engine
        self.SqliteSessionLocal = SessionLocal

    def init_local_schema(self) -> None:
        init_dev2_db()

    def get_local_session(self) -> Session:
        db = SessionLocal()
        db.info["store"] = get_shared_store()
        return db

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        session = self.get_local_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


db_manager = _CompatDatabaseManager()

__all__ = [
    "Base",
    "DATABASE_URL",
    "SessionLocal",
    "db_manager",
    "engine",
    "get_db",
    "get_shared_store",
    "init_dev2_db",
    "register_shared_runtime",
]