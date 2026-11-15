from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dev1_bridge import ActorContext, get_actor_context
from app.models.dev2_models import MissionLocation, RadiationAreaRecord, new_uuid
from app.radiation.service import RadiationService
from app.schemas.dev2_schemas import PersonalDoseCreate, SpeEventCreate

router = APIRouter(prefix="/radiation", tags=["radiation"])


class AreaDoseCreate(BaseModel):
    event_id: Optional[str] = None
    location_id: str
    sensor_id: str
    radiation_metric: str
    value: float
    unit: str
    measured_at: datetime
    source_type: str = "SIMULATED"
    is_synthetic: bool = True


@router.post("/personal-dose", status_code=201)
def record_personal_dose(
    payload: PersonalDoseCreate,
    db: Session = Depends(get_db),
    _actor: ActorContext = Depends(get_actor_context),
):
    return RadiationService.ingest_personal_dose(db, payload)


@router.post("/area-dose", status_code=201)
def record_area_dose(
    payload: AreaDoseCreate,
    db: Session = Depends(get_db),
    _actor: ActorContext = Depends(get_actor_context),
):
    """T15: Record cabin/zone area radiation telemetry without assuming unverified shielding factors."""
    rec = RadiationAreaRecord(
        event_id=payload.event_id or new_uuid(),
        location_id=payload.location_id,
        sensor_id=payload.sensor_id,
        radiation_metric=payload.radiation_metric,
        value=payload.value,
        unit=payload.unit,
        measured_at=payload.measured_at,
        source_type=payload.source_type,
        is_synthetic=payload.is_synthetic,
    )
    db.add(rec)
    db.flush()
    return {"id": rec.id, "location_id": rec.location_id, "value": rec.value, "unit": rec.unit}


@router.get("/locations")
def list_mission_locations(
    db: Session = Depends(get_db),
    _actor: ActorContext = Depends(get_actor_context),
):
    locs = db.scalars(select(MissionLocation)).all()
    return {
        "items": [
            {
                "location_code": loc.location_code,
                "zone_name": loc.zone_name,
                "location_type": loc.location_type,
                "is_spe_shelter": loc.is_spe_shelter,
                "shielding_notes": loc.shielding_notes,
            }
            for loc in locs
        ]
    }


@router.post("/spe-events", status_code=201)
def trigger_spe(
    payload: SpeEventCreate,
    crew_ids: List[str] = Query(default=["CREW-01", "CREW-02", "CREW-03", "CREW-04"]),
    db: Session = Depends(get_db),
    _actor: ActorContext = Depends(get_actor_context),
):
    return RadiationService.trigger_spe_event(db, payload, crew_ids)


@router.get("/astronauts/{astronaut_id}/cumulative")
def get_cumulative_dose(
    astronaut_id: str,
    db: Session = Depends(get_db),
    _actor: ActorContext = Depends(get_actor_context),
):
    return RadiationService.get_astronaut_cumulative_dose(db, astronaut_id)