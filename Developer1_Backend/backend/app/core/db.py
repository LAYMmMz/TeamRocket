from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Generator, Optional

from fastapi import Request
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.models.dev2_models import Base
from app.cloud_completion.outbox import ClinicalCloudOutbox, activate, drain  # TEAMROCKET_CLINICAL_OUTBOX_V1

# Default offline-first SQLite database; overridden by DATABASE_URL (e.g., Supabase Postgres) when set
DEFAULT_SQLITE_URL = "sqlite:///./data/dev2_clinical.db"
# Dev2 storage is a separate LOCAL PROTOTYPE database; never auto-create Supabase tables.
DATABASE_URL = os.getenv("DEV2_DATABASE_URL") or DEFAULT_SQLITE_URL
if not DATABASE_URL.startswith("sqlite:///"):
    raise RuntimeError("Dev2 must use a local SQLite URL; cloud integration requires reviewed migrations")

if DATABASE_URL.startswith("sqlite:///"):
    db_file = DATABASE_URL.replace("sqlite:///", "", 1)
    if db_file and db_file != ":memory:":
        Path(db_file).parent.mkdir(parents=True, exist_ok=True)

connect_args = (
    {"check_same_thread": False, "timeout": 30}
    if DATABASE_URL.startswith("sqlite")
    else {}
)

engine: Engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    future=True,
)


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection: Any, _connection_record: Any) -> None:
    module_name = type(dbapi_connection).__module__
    if "sqlite3" in module_name:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA busy_timeout=30000;")
        cursor.close()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

_SHARED_STORE: Any = None
_SHARED_SETTINGS: Any = None


def register_shared_runtime(store: Any, settings: Any) -> None:
    """Called by app lifespan so CLI scripts and background tasks share Dev 1's live Store."""
    global _SHARED_STORE, _SHARED_SETTINGS
    _SHARED_STORE = store
    _SHARED_SETTINGS = settings


def get_shared_store() -> Any:
    """Returns Dev 1's encrypted Store instance (initializing lazily for standalone CLI scripts)."""
    global _SHARED_STORE, _SHARED_SETTINGS
    if _SHARED_STORE is not None:
        return _SHARED_STORE
    try:
        from app.core import config as core_config
        from app.core.config import Settings
        from app.offline.store import Store

        if _SHARED_SETTINGS is None:
            _SHARED_SETTINGS = (
                core_config.get_settings()
                if hasattr(core_config, "get_settings")
                else Settings()
            )
        Path(_SHARED_SETTINGS.sqlite_path).parent.mkdir(parents=True, exist_ok=True)
        _SHARED_STORE = Store(_SHARED_SETTINGS)
    except Exception:
        _SHARED_STORE = None
    return _SHARED_STORE


def init_dev2_db(bind: Optional[Engine] = None) -> None:
    """Creates all Dev 2 tables in SQLite or Supabase PostgreSQL if they do not exist."""
    Base.metadata.create_all(bind=bind or engine)


def get_db(request: Request) -> Generator[Session, None, None]:
    """FastAPI dependency injecting a SQLAlchemy Session linked to Dev 1's Store & Settings."""
    db = SessionLocal()
    activate(db)  # TEAMROCKET_CLINICAL_OUTBOX_V1
    db.info["store"] = getattr(request.app.state, "store", None) or get_shared_store()
    db.info["settings"] = getattr(request.app.state, "settings", None) or _SHARED_SETTINGS
    try:
        yield db
        db.commit()
        store = db.info.get("store")
        if store is not None:
            drain(store, SessionLocal)  # TEAMROCKET_CLINICAL_OUTBOX_V1
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
# TEAMROCKET_UNIFIED_CLOUD_V2: unified RPC integration enabled
