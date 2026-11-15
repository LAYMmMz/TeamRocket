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

    return ingest(
        record,
        store,
        settings,
        principal.user_id,
    )


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