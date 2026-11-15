# backend/app/environment/router.py
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.environment.service import EnvironmentService
from app.schemas.dev2_schemas import EnvironmentalReadingCreate, EnvironmentalSampleCreate

router = APIRouter(tags=["Cabin Environment & Microbiology"])


@router.post("/api/environment/readings")
def post_environment_reading(payload: EnvironmentalReadingCreate, db: Session = Depends(get_db)):
    return EnvironmentService.ingest_reading(db, payload)


@router.post("/api/environment/microbiology")
def post_microbiology_sample(payload: EnvironmentalSampleCreate, db: Session = Depends(get_db)):
    return EnvironmentService.ingest_microbiology_sample(db, payload)