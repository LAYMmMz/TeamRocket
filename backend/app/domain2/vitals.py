"""Domain-specific vital sign endpoint reuses canonical Dev 1 ingestor and alerts."""
from fastapi import APIRouter, Depends
from app.auth.dependencies import require
from app.core.dependencies import get_settings,get_store
from app.core.errors import AppError
from app.measurements.models import Measurement
from app.measurements.service import ingest
router=APIRouter(tags=["Developer 2 vital signs"])
VITALS={"heart_rate","spo2","respiratory_rate","systolic_bp","diastolic_bp","temperature"}
@router.post("/vitals",status_code=201)
def vital(record:Measurement,principal=Depends(require("measurements:write")),store=Depends(get_store),settings=Depends(get_settings)):
    principal.require_mission(record.mission_id)
    if record.metric not in VITALS:
        raise AppError(422,"vital_metric_required","Use /api/measurements for other measurements")
    return ingest(record,store,settings,principal.user_id)
