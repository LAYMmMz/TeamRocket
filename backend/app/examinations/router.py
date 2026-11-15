# backend/app/examinations/router.py
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.examinations.service import ExaminationsService
from app.schemas.dev2_schemas import BoneScanCreate, OcularAssessmentCreate, VascularUltrasoundCreate

router = APIRouter(tags=["Clinical Examinations (Scheduler, Vascular, Ocular, DXA)"])


@router.get("/api/examinations/{astronaut_id}/schedule")
def get_schedule(astronaut_id: str, mission_phase: str = "IN_FLIGHT_NORMAL", db: Session = Depends(get_db)):
    return ExaminationsService.get_exam_schedule(db, astronaut_id, current_mission_phase=mission_phase)


@router.post("/api/examinations/vascular")
def post_vascular_ultrasound(payload: VascularUltrasoundCreate, db: Session = Depends(get_db)):
    return ExaminationsService.record_vascular_ultrasound(db, payload)


@router.post("/api/examinations/ocular")
def post_ocular_assessment(payload: OcularAssessmentCreate, db: Session = Depends(get_db)):
    return ExaminationsService.record_ocular_assessment(db, payload)


@router.get("/api/examinations/{astronaut_id}/ocular/{eye}")
def get_ocular_trend(
    astronaut_id: str,
    eye: str,
    scan_region: str = "RNFL_GLOBAL",
    metric_code: str = "RNFL_THICKNESS",
    db: Session = Depends(get_db),
):
    return ExaminationsService.get_ocular_eye_trend(db, astronaut_id, eye, scan_region, metric_code)


@router.post("/api/examinations/dxa")
def post_bone_scan(payload: BoneScanCreate, db: Session = Depends(get_db)):
    return ExaminationsService.record_bone_scan(db, payload)


@router.get("/api/examinations/{astronaut_id}/dxa/{bone_region}")
def get_dxa_comparison(astronaut_id: str, bone_region: str, db: Session = Depends(get_db)):
    return ExaminationsService.compare_dxa_same_region(db, astronaut_id, bone_region.upper())