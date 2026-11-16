from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dev1_bridge import ActorContext, Dev1IntegrationBridge, get_actor_context
from app.incidents.service import ingest_serious_symptom
from app.models.dev2_models import EcgRecord, HealthBaseline, SymptomReport, VitalSign, new_uuid
from app.schemas.dev2_schemas import ExerciseSessionCreate, VitalCreate, VitalOut
from app.vitals.service import VitalsService

router = APIRouter(tags=["vitals & symptoms"])


class EcgRecordCreate(BaseModel):
    event_id: Optional[str] = None
    astronaut_id: str
    mission_id: str = "DEMO-01"
    start_at: datetime
    end_at: datetime
    waveform_reference: str
    reviewed_interpretation: Optional[str] = None
    reviewer_id: Optional[str] = None
    measured_at: datetime
    source_type: str = "SIMULATED"
    is_synthetic: bool = True


class SymptomCreate(BaseModel):
    event_id: Optional[str] = None
    astronaut_id: str
    mission_id: str = "DEMO-01"
    symptom_code: str
    severity: str = Field(pattern="^(MILD|MODERATE|SERIOUS|SEVERE|CRITICAL)$")
    onset_at: datetime
    body_location: str
    measured_at: datetime
    source_type: str = "SIMULATED"
    is_synthetic: bool = True


@router.post("/clinical/vitals", response_model=VitalOut, status_code=201)
def create_vital(
    payload: VitalCreate,
    db: Session = Depends(get_db),
    actor: ActorContext = Depends(get_actor_context),
):
    Dev1IntegrationBridge.record_audit(db, actor, "INGEST_VITAL", "vital_signs", payload.astronaut_id)
    return VitalsService.ingest_vital(db, payload)


@router.post("/vitals/biomonitor-batch", status_code=201)
def ingest_biomonitor_batch(
    records: List[VitalCreate],
    db: Session = Depends(get_db),
    actor: ActorContext = Depends(get_actor_context),
):
    """T14: Multi-metric Bio-Monitor batch import without assuming continuous wearable connection."""
    results = [VitalsService.ingest_vital(db, rec) for rec in records]
    Dev1IntegrationBridge.record_audit(db, actor, "INGEST_BIOMONITOR_BATCH", "vital_signs", f"count={len(results)}")
    return {"ingested": len(results), "items": results}


@router.post("/vitals/ecg", status_code=201)
def create_ecg_record(
    payload: EcgRecordCreate,
    db: Session = Depends(get_db),
    actor: ActorContext = Depends(get_actor_context),
):
    """T14: Store ECG waveform references separately from clinician-reviewed interpretations."""
    rec = EcgRecord(
        event_id=payload.event_id or new_uuid(),
        astronaut_id=payload.astronaut_id,
        mission_id=payload.mission_id,
        start_at=payload.start_at,
        end_at=payload.end_at,
        waveform_reference=payload.waveform_reference,
        reviewed_interpretation=payload.reviewed_interpretation,
        reviewer_id=payload.reviewer_id,
        measured_at=payload.measured_at,
        source_type=payload.source_type,
        is_synthetic=payload.is_synthetic,
        verification_status="VERIFIED" if payload.reviewer_id else "UNREVIEWED",
    )
    db.add(rec)
    db.flush()
    Dev1IntegrationBridge.enqueue_sync(
        db=db,
        event_id=rec.event_id,
        resource_type="ecg_records",
        priority=3,
        payload={"id": rec.id, "astronaut_id": rec.astronaut_id, "waveform_reference": rec.waveform_reference},
        mission_id=payload.mission_id,
    )
    return {"id": rec.id, "event_id": rec.event_id, "verification_status": rec.verification_status}


@router.get("/vitals/{astronaut_id}")
def get_latest_vitals(
    astronaut_id: str,
    stale_after_minutes: int = Query(default=120, ge=1),
    db: Session = Depends(get_db),
    _actor: ActorContext = Depends(get_actor_context),
):
    return VitalsService.get_latest_vitals(db, astronaut_id, stale_after_minutes=stale_after_minutes)


@router.post("/vitals/baselines/{astronaut_id}/recalculate")
def recalculate_baselines(
    astronaut_id: str,
    db: Session = Depends(get_db),
    _actor: ActorContext = Depends(get_actor_context),
):
    """T09: Recompute personal baselines when delayed/out-of-order telemetry arrives."""
    metrics = ["HR", "SPO2", "RR", "BP_SYS", "BP_DIA", "TEMP"]
    updated = {}
    for metric in metrics:
        rows = db.scalars(
            select(VitalSign).where(
                VitalSign.astronaut_id == astronaut_id,
                VitalSign.metric_code == metric,
                VitalSign.quality_status == "VALID",
                VitalSign.activity_context == "RESTING",
            )
        ).all()
        if not rows:
            updated[metric] = {"status": "BASELINE_UNAVAILABLE"}
            continue
        mean_val = round(sum(r.normalized_value for r in rows) / len(rows), 3)
        unit = rows[0].normalized_unit
        existing = db.scalars(
            select(HealthBaseline).where(
                HealthBaseline.astronaut_id == astronaut_id,
                HealthBaseline.metric_code == metric,
            )
        ).first()
        if existing:
            existing.baseline_value = mean_val
            existing.sample_count = len(rows)
        else:
            db.add(
                HealthBaseline(
                    astronaut_id=astronaut_id,
                    metric_code=metric,
                    baseline_value=mean_val,
                    unit=unit,
                    sample_count=len(rows),
                )
            )
        updated[metric] = {"status": "AVAILABLE", "baseline_value": mean_val, "unit": unit, "samples": len(rows)}
    db.flush()
    return {"astronaut_id": astronaut_id, "baselines": updated}


@router.post("/vitals/exercise-sessions", status_code=201)
def log_exercise(
    payload: ExerciseSessionCreate,
    db: Session = Depends(get_db),
    _actor: ActorContext = Depends(get_actor_context),
):
    session = VitalsService.log_exercise_session(db, payload)
    return {"id": session.id, "astronaut_id": session.astronaut_id, "exercise_type": session.exercise_type}


@router.post("/symptoms", status_code=201)
def report_symptom(
    payload: SymptomCreate,
    db: Session = Depends(get_db),
    actor: ActorContext = Depends(get_actor_context),
):
    """
    T10 & S03: Unified symptom endpoint accepting all severities.
    Delegates SERIOUS/SEVERE/CRITICAL symptoms directly to Dev 1's incident workflow even with zero sensors.
    """
    ev_id = payload.event_id or new_uuid()
    symptom = SymptomReport(
        event_id=ev_id,
        astronaut_id=payload.astronaut_id,
        mission_id=payload.mission_id,
        symptom_code=payload.symptom_code,
        severity=payload.severity,
        onset_at=payload.onset_at,
        body_location=payload.body_location,
        measured_at=payload.measured_at,
        source_type=payload.source_type,
        is_synthetic=payload.is_synthetic,
    )
    db.add(symptom)
    db.flush()

    incident_out = None
    if payload.severity in {"SERIOUS", "SEVERE", "CRITICAL"}:
        res = Dev1IntegrationBridge.emit_alert_and_optional_incident(
            db=db,
            rule_id="RULE-SERIOUS-SYMPTOM-ESCALATION",
            rule_version="1.0.0",
            rule_approval_status="APPROVED",
            severity="CRITICAL",
            title=f"Serious symptom reported ({payload.symptom_code} - {payload.severity}) — immediate clinical review",
            evidence_refs=[f"symptom_reports:{symptom.id}"],
            astronaut_id=payload.astronaut_id,
            open_incident=True,
            incident_type="SERIOUS_SYMPTOM_EMERGENCY",
            is_synthetic=payload.is_synthetic,
            mission_id=payload.mission_id,
        )
        incident_out = res["incident_id"]

        store = db.info.get("store")
        settings = db.info.get("settings")
        if store is not None and settings is not None:
            dev1_inc = ingest_serious_symptom(
                {
                    "event_id": ev_id,
                    "mission_id": payload.mission_id,
                    "astronaut_id": payload.astronaut_id,
                    "symptom": payload.symptom_code,
                    "severity": payload.severity.lower(),
                    "onset": payload.onset_at.isoformat(),
                    "body_location": payload.body_location,
                    "source_type": payload.source_type,
                    "is_synthetic": payload.is_synthetic,
                    "measured_at": payload.measured_at.isoformat(),
                    "received_at": symptom.received_at.isoformat(),
                    "quality": "VALID",
                    "verification": "UNVERIFIED",
                },
                store,
                settings,
                actor.user_id,
            )
            incident_out = dev1_inc.get("incident_id", incident_out)

    Dev1IntegrationBridge.enqueue_sync(
        db=db,
        event_id=ev_id,
        resource_type="symptom_reports",
        priority=0 if payload.severity in {"SERIOUS", "SEVERE", "CRITICAL"} else 3,
        payload={"id": symptom.id, "symptom_code": payload.symptom_code, "severity": payload.severity},
        mission_id=payload.mission_id,
    )
    # TEAMROCKET_DEV2_SYMPTOM_CLOUD_V1
    # The Dev2 SQLAlchemy queue is local-only. Mirror the supported synthetic
    # symptom into Dev1's encrypted Store, whose worker uses the cloud RPC.
    # This does not enable cloud sync for unrelated Dev2 record types.
    store = db.info.get("store")
    settings = db.info.get("settings")
    if (
        store is not None
        and settings is not None
        and settings.environment in {"development", "test"}
        and payload.is_synthetic
        and payload.source_type == "SIMULATED"
    ):
        cloud_payload = {
            "event_id": ev_id,
            "mission_id": payload.mission_id,
            "astronaut_id": payload.astronaut_id,
            "symptom_code": payload.symptom_code,
            "symptom": payload.symptom_code,
            "severity": payload.severity,
            "onset_at": payload.onset_at.isoformat(),
            "body_location": payload.body_location,
            "measured_at": payload.measured_at.isoformat(),
            "recorded_at": payload.measured_at.isoformat(),
            "source_type": payload.source_type,
            "is_synthetic": True,
            "quality": "VALID",
            "verification": "UNVERIFIED",
            "source_reference": "dev2-synthetic-symptom-api",
            "source_revision": "v1",
        }
        store.put(
            "symptom", ev_id, cloud_payload,
            mission_id=payload.mission_id,
            actor_id=actor.user_id,
            priority=10,
        )

    return {"id": symptom.id, "event_id": ev_id, "severity": payload.severity, "incident_id": incident_out}


@router.get("/symptoms")
def list_symptoms(
    astronaut_id: Optional[str] = None,
    db: Session = Depends(get_db),
    _actor: ActorContext = Depends(get_actor_context),
):
    stmt = select(SymptomReport).order_by(SymptomReport.reported_at.desc())
    if astronaut_id:
        stmt = stmt.where(SymptomReport.astronaut_id == astronaut_id)
    rows = db.scalars(stmt).all()
    return {
        "items": [
            {
                "id": r.id,
                "astronaut_id": r.astronaut_id,
                "symptom_code": r.symptom_code,
                "severity": r.severity,
                "body_location": r.body_location,
                "reported_at": r.reported_at.isoformat(),
                "is_synthetic": r.is_synthetic,
            }
            for r in rows
        ]
    }