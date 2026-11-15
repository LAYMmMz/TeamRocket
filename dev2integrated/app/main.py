from __future__ import annotations

from contextlib import asynccontextmanager
import importlib
import importlib.util
import logging
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core import config as core_config
from app.core.config import Settings
from app.core.db import DATABASE_URL, init_dev2_db, register_shared_runtime

logger = logging.getLogger("nasa_health_monitor")


def _try_import_router(module_path: str):
    try:
        if importlib.util.find_spec(module_path) is None:
            return None
        mod = importlib.import_module(module_path)
        return getattr(mod, "router", None)
    except ModuleNotFoundError:
        return None
    except Exception as exc:
        logger.warning("Router %s failed to load: %s", module_path, exc)
        return None


def _load_default_settings() -> Settings:
    if hasattr(core_config, "get_settings"):
        return core_config.get_settings()
    if hasattr(Settings, "from_env"):
        return Settings.from_env()
    return Settings()


def _init_dev1_store(cfg: Settings):
    from app.offline.store import Store

    Path(cfg.sqlite_path).parent.mkdir(parents=True, exist_ok=True)
    return Store(cfg)


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    cfg = settings or _load_default_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # 1. Initialize Dev 2 SQLAlchemy tables (SQLite offline or Supabase Postgres)
        init_dev2_db()

        # 2. Initialize Dev 1 encrypted SQLite Store & background SyncWorker
        store = None
        worker = None
        try:
            store = _init_dev1_store(cfg)
        except Exception as exc:
            logger.error("Dev 1 Store init failed: %s", exc)

        app.state.settings = cfg
        app.state.store = store
        register_shared_runtime(store, cfg)

        try:
            from app.sync.worker import SyncWorker

            if store is not None:
                worker = SyncWorker(store, cfg)
                worker.start()
        except Exception as exc:
            logger.info("SyncWorker running in manual/offline mode: %s", exc)

        yield

        if worker is not None:
            try:
                worker.stop()
            except Exception:
                pass

    app = FastAPI(
        title="NASA Deep-Space Crew Health Monitoring System (Unified Dev 1 + Dev 2)",
        version="2.0.0",
        description="Offline-first modular monolith supporting local SQLite, cloud Supabase sync, and React dashboards.",
        lifespan=lifespan,
    )

    # CORS for React (Vite dev server + Vercel production)
    allowed_origins = [
        o.strip()
        for o in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000",
        ).split(",")
        if o.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request body size guard (max 2 MB) & Dev 1 JWT Principal extraction
    @app.middleware("http")
    async def security_and_size_middleware(request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 2 * 1024 * 1024:
            return JSONResponse(
                status_code=413,
                content={"error": {"code": "PAYLOAD_TOO_LARGE", "message": "Request body exceeds 2 MB limit."}},
            )

        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1].strip()
            try:
                from app.core.security import decode_access_token

                request.state.principal = decode_access_token(token, cfg)
            except Exception:
                request.state.principal = None

        return await call_next(request)

    # Unified Error Envelope across Dev 1 and Dev 2 routes
    @app.exception_handler(HTTPException)
    async def http_exception_handler(_request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "error": {"code": f"HTTP_{exc.status_code}", "message": str(exc.detail)},
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "detail": exc.errors(),
                "error": {"code": "VALIDATION_ERROR", "message": "Invalid request payload."},
            },
        )

    @app.get("/api/health", tags=["system"])
    def health_check(request: Request):
        store_ok = getattr(request.app.state, "store", None) is not None
        db_backend = "supabase_postgres" if DATABASE_URL.startswith("postgres") else "sqlite_offline"
        return {
            "status": "ok",
            "environment": cfg.environment,
            "clinical_db": db_backend,
            "encrypted_store_ready": store_ok,
            "offline_capable": True,
        }

    # Mount Dev 1 Routers
    dev1_modules = [
        "app.auth.router",
        "app.foundation.router",
        "app.measurements.router",
        "app.alerts.router",
        "app.incidents.router",
        "app.procedures.router",
        "app.inventory.router",
        "app.sync.router",
        "app.integrations.router",
    ]
    for mod_path in dev1_modules:
        r = _try_import_router(mod_path)
        if r is not None:
            app.include_router(r)

    # Mount Dev 2 Routers
    dev2_modules = [
        "app.vitals.router",
        "app.radiation.router",
        "app.environment.router",
        "app.wellness.router",
        "app.examinations.router",
        "app.samples.router",
        "app.reports.router",
        "app.simulation.router",
        "app.nasa.router",
    ]
    for mod_path in dev2_modules:
        r = _try_import_router(mod_path)
        if r is not None:
            app.include_router(r)

    return app


app = create_app()