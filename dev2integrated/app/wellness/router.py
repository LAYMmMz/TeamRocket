from __future__ import annotations

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dev1_bridge import ActorContext, Dev1IntegrationBridge, get_actor_context
from app.models.dev2_models import (
    BehavioralCheckin,
    FluidBalanceLog,
    FunctionalAssessment,
    GravityTransitionEvent,
    SleepSession,
    new_uuid,
)

router = APIRouter(prefix="/wellness", tags=["wellness, gravity & behavioral"])


class GravityTransitionCreate(BaseModel):
    event_id: Optional[str] = None
    mission_id: str = "DEMO-01"
    from_g: float
    to_g: float
    occurred_at: datetime
    adaptation_window_hours: int = 72
    source_type: str = "SIMULATED"
    is_synthetic: bool = True


class FunctionalAssessmentCreate(BaseModel):
    event_id: Optional[str] = None
    astronaut_id: str
    transition_event_id: Optional[str] = None
    test_type: str = "REACTION_TIME"
    reaction_time_ms: Optional[float] = None
    symptom_score_10: Optional[float] = None
    assessed_at: datetime
    source_type: str = "SIMULATED"
    is_synthetic: bool = True


class FluidBalanceCreate(BaseModel):
    event_id: Optional[str] = None
    astronaut_id: str
    period_start: datetime
    period_end: datetime
    intake_ml: float
    output_ml: float
    source_type: str = "SIMULATED"
    is_synthetic: bool = True


class BehavioralCheckinCreate(BaseModel):
    event_id: Optional[str] = None
    astronaut_id: str
    assessment_type: str = "MOOD_FATIGUE"
    score: float
    visibility_classification: str = "PRIVATE_CLINICAL"
    notes: Optional[str] = None
    measured_at: datetime
    source_type: str = "SIMULATED"
    is_synthetic: bool = True


@router.post("/gravity-transitions", status_code=201)
def record_gravity_transition(
    payload: GravityTransitionCreate,
    db: Session = Depends(get_db),
    _actor: ActorContext = Depends(get_actor_context),
):
    """T17: Opens gravity adaptation window; EVA clearance strictly remains PENDING_HUMAN_REVIEW."""
    ev = GravityTransitionEvent(
        event_id=payload.event_id or new_uuid(),
        mission_id=payload.mission_id,
        from_g=payload.from_g,
        to_g=payload.to_g,
        occurred_at=payload.occurred_at,
        adaptation_window_hours=payload.adaptation_window_hours,
        parameter_classification="RESEARCH_ONLY",
        eva_clearance_status="PENDING_HUMAN_REVIEW",
        source_type=payload.source_type,
        is_synthetic=payload.is_synthetic,
    )
    db.add(ev)
    db.flush()
    return {
        "id": ev.id,
        "from_g": ev.from_g,
        "to_g": ev.to_g,
        "adaptation_window_hours": ev.adaptation_window_hours,
        "parameter_classification": "RESEARCH_ONLY",
        "eva_clearance_status": "PENDING_HUMAN_REVIEW",
        "autonomous_eva_decision": False,
    }


@router.post("/functional-assessments", status_code=201)
def record_functional_assessment(
    payload: FunctionalAssessmentCreate,
    db: Session = Depends(get_db),
    _actor: ActorContext = Depends(get_actor_context),
):
    """T17: 500 ms reaction time & 3/10 symptom cutoff are RESEARCH_ONLY; never auto-approves/denies EVA."""
    exceeded = bool(
        (payload.reaction_time_ms is not None and payload.reaction_time_ms > 500.0)
        or (payload.symptom_score_10 is not None and payload.symptom_score_10 > 3.0)
    )
    rec = FunctionalAssessment(
        event_id=payload.event_id or new_uuid(),
        astronaut_id=payload.astronaut_id,
        transition_event_id=payload.transition_event_id,
        test_type=payload.test_type,
        reaction_time_ms=payload.reaction_time_ms,
        symptom_score_10=payload.symptom_score_10,
        research_threshold_exceeded=exceeded,
        eva_clearance_status="PENDING_HUMAN_REVIEW",
        assessed_at=payload.assessed_at,
        source_type=payload.source_type,
        is_synthetic=payload.is_synthetic,
    )
    db.add(rec)
    db.flush()
    return {
        "id": rec.id,
        "research_threshold_exceeded": exceeded,
        "parameter_classification": "RESEARCH_ONLY",
        "eva_clearance_status": "PENDING_HUMAN_REVIEW",
    }


@router.post("/hydration", status_code=201)
def record_hydration(
    payload: FluidBalanceCreate,
    db: Session = Depends(get_db),
    _actor: ActorContext = Depends(get_actor_context),
):
    """T17: Fluid intake/output tracking."""
    log = FluidBalanceLog(
        event_id=payload.event_id or new_uuid(),
        astronaut_id=payload.astronaut_id,
        period_start=payload.period_start,
        period_end=payload.period_end,
        intake_ml=payload.intake_ml,
        output_ml=payload.output_ml,
        source_type=payload.source_type,
        is_synthetic=payload.is_synthetic,
    )
    db.add(log)
    db.flush()
    return {"id": log.id, "net_balance_ml": round(log.intake_ml - log.output_ml, 1), "unit": "mL"}


@router.post("/checkins", status_code=201)
def create_behavioral_checkin(
    payload: BehavioralCheckinCreate,
    db: Session = Depends(get_db),
    actor: ActorContext = Depends(get_actor_context),
):
    rec = BehavioralCheckin(
        event_id=payload.event_id or new_uuid(),
        astronaut_id=payload.astronaut_id,
        assessment_type=payload.assessment_type,
        score=payload.score,
        visibility_classification=payload.visibility_classification,
        notes=payload.notes,
        measured_at=payload.measured_at,
        source_type=payload.source_type,
        is_synthetic=payload.is_synthetic,
    )
    db.add(rec)
    db.flush()
    Dev1IntegrationBridge.record_audit(db, actor, "WRITE_BEHAVIORAL_CHECKIN", "behavioral_checkins", rec.id)
    return {"id": rec.id, "visibility_classification": rec.visibility_classification}


@router.get("/behavioral/{astronaut_id}")
def get_behavioral_checkins(
    astronaut_id: str,
    db: Session = Depends(get_db),
    actor: ActorContext = Depends(get_actor_context),
):
    """T18 & S12: Enforces PRIVATE_CLINICAL RBAC and writes denied attempts to audit ledger."""
    rows = db.scalars(
        select(BehavioralCheckin).where(BehavioralCheckin.astronaut_id == astronaut_id)
    ).all()
    for r in rows:
        Dev1IntegrationBridge.enforce_behavioral_privacy(db, actor, astronaut_id, r.visibility_classification)
    Dev1IntegrationBridge.record_audit(db, actor, "READ_BEHAVIORAL_CHECKIN", "behavioral_checkins", astronaut_id)
    return {
        "astronaut_id": astronaut_id,
        "items": [
            {
                "id": r.id,
                "assessment_type": r.assessment_type,
                "score": r.score,
                "visibility_classification": r.visibility_classification,
                "measured_at": r.measured_at.isoformat(),
            }
            for r in rows
        ],
    }


@router.get("/{astronaut_id}")
def get_wellness_summary(
    astronaut_id: str,
    db: Session = Depends(get_db),
    _actor: ActorContext = Depends(get_actor_context),
):
    sleeps = db.scalars(
        select(SleepSession).where(SleepSession.astronaut_id == astronaut_id).order_by(SleepSession.end_at.desc())
    ).all()
    if not sleeps:
        return {"astronaut_id": astronaut_id, "sleep_status": "DATA_UNAVAILABLE", "latest_sleep_minutes": None}
    latest = sleeps[0]
    return {
        "astronaut_id": astronaut_id,
        "sleep_status": latest.quality_status,
        "latest_sleep_minutes": latest.duration_minutes,
        "iss_historical_context_note": "6.0-6.5 hr ISS average is historical context only, not a clinical goal.",
    }