"""TeamRocket measurement endpoints with development-only team SQLite mirror."""
import logging

from fastapi import APIRouter, Depends

from app.auth.dependencies import require
from app.core.dependencies import get_settings, get_store
from app.measurements.models import Measurement
from app.measurements.service import ingest

# Compatibility exports for earlier imports.
from app.measurements.units import UNITS, validate_domain

router = APIRouter(tags=["measurements"])


@router.post("/measurements", status_code=201)
def create_measurement(
    record: Measurement,
    principal=Depends(require("measurements:write")),
    store=Depends(get_store),
    settings=Depends(get_settings),
):
    principal.require_mission(record.mission_id)

    # Existing encrypted store remains authoritative. This operation already
    # validates, audits, evaluates rules, and enqueues cloud synchronization.
    result = ingest(record, store, settings, principal.user_id)

    # Development-only, best-effort projection into teammate's plaintext DB.
    # No real clinical data, no second cloud sync/outbox, no change to 201 on
    # a mirror failure. Replay missing data with team_sqlite_bridge.py.
    if settings.environment == "development" and record.is_synthetic:
        try:
            from team_sqlite_bridge import mirror_record
            result["team_sqlite_mirror"] = mirror_record(result["measurement"])
        except Exception:
            logging.getLogger(__name__).exception(
                "Development team SQLite mirror failed"
            )
            result["team_sqlite_mirror"] = "error"

    return result


@router.get("/measurements")
def list_measurements(
    mission_id: str,
    principal=Depends(require("measurements:read")),
    store=Depends(get_store),
):
    principal.require_mission(mission_id)
    return {
        "items": store.list(
            "measurement",
            mission_id=mission_id,
        )
    }
