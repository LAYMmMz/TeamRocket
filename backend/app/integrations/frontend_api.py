"""Versioned, role-gated adapter for the RocketPulse React frontend.

This layer maps the existing local-first APIs and synthetic Dev2 SQLite fixtures
to the DTOs in frontend/src/lib/types.ts. It does not bypass the authoritative
Store, turn demo fixtures into clinical readings, or initialize Supabase tables.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.auth.dependencies import require
from app.core.dependencies import get_settings, get_store
from app.core.errors import AppError
from app.measurements.models import Measurement

router = APIRouter(prefix="/api/v1", tags=["RocketPulse frontend compatibility"])
MISSION = "DEMO-01"

DOMAIN_TABLES = {
    "cardiorespiratory": ("VitalSign", "EcgRecord", "HealthBaseline", "SymptomReport"),
    "vascular": ("VascularUltrasoundResult", "LaboratoryResult"),
    "radiation": ("PersonalDoseRecord", "RadiationAreaRecord", "RadiationEvent"),
    "gravity": ("GravityTransitionEvent", "FunctionalAssessment", "FluidBalanceLog"),
    "fitness": ("FitnessAssessment", "ExerciseSession", "FunctionalAssessment"),
    "bone": ("BoneScan", "BoneDensityResult", "ExerciseSession"),
    "vision": ("OcularAssessment", "OcularResult"),
    "immune": ("BiologicalSample", "LaboratoryResult", "ClinicalSampleChain"),
    "sleep": ("SleepSession",),  # confidential behavioral notes deliberately excluded
    "cabin": ("EnvironmentalReading", "MissionLocation"),
    "microbiology": ("EnvironmentalSample", "EnvironmentalLabResult", "SequencingRun"),
    "medicalops": ("LocalMedicalIncident",),
}
DOMAIN_STORE = {
    "cardiorespiratory": ("measurement", "dev2_symptoms"),
    "vascular": ("dev2_vascular",),
    "radiation": ("dev2_radiation",),
    "gravity": ("dev2_gravity",),
    "fitness": ("dev2_fitness",),
    "bone": ("dev2_bone",),
    "vision": ("dev2_ocular",),
    "immune": ("dev2_lab_results",),
    "sleep": ("dev2_sleep",),
    "cabin": ("dev2_environment",),
    "microbiology": ("dev2_environmental_results",),
    "medicalops": ("incident",),
}



@router.post("/measurements", status_code=201)
def ingest_synthetic_measurement(
    record: "Measurement",
    principal=Depends(require("measurements:write")),
    store=Depends(get_store),
    settings=Depends(get_settings),
):
    """V1 synthetic-only ingestion for an explicit end-to-end test.

    The authoritative measurement service performs provenance validation,
    encrypted SQLite persistence and outbox enqueue; it never writes from
    the browser directly to Supabase.
    """
    from app.measurements.service import ingest
    principal.require_mission(record.mission_id)
    if not record.is_synthetic or record.source_type != "SIMULATED":
        raise AppError(403, "synthetic_test_only",
                       "This integration test accepts synthetic measurements only")
    if settings.environment not in {"development", "test"}:
        raise AppError(403, "synthetic_data_disabled",
                       "Synthetic test ingestion is disabled in production")
    return ingest(record, store, settings, principal.user_id)

def now_iso():
    return datetime.now(timezone.utc).isoformat()


def iso(value):
    return value.isoformat() if isinstance(value, datetime) else str(value or "")


def verification(value):
    return {
        "VERIFIED": "verified-demo",
        "UNVERIFIED": "unreviewed",
        "DEMO_ONLY": "review-required",
        "RESEARCH_ONLY": "review-required",
        "REJECTED": "review-required",
    }.get(str(value or "").upper(), "review-required")


def quality(value):
    return {
        "VALID": "ok", "SUSPECT": "review-required", "INVALID": "review-required",
        "MISSING": "missing", "STALE": "stale",
    }.get(str(value or "").upper(), "review-required")


def source(value):
    return {
        "SIMULATED": "synthetic", "RESEARCH": "research-only", "REAL": "imported"
    }.get(str(value or "").upper(), "research-only")


def authorized(principal, mission_id):
    principal.require_mission(mission_id)


def read_dev2(model_name, mission_id, astronaut_id, settings, limit=40):
    """Read explicitly synthetic, local demo fixtures; never mix mission scopes."""
    if settings.environment not in {"development", "test"} or mission_id != MISSION:
        return []
    from app.models import dev2_models
    from app.core.db import SessionLocal
    model = getattr(dev2_models, model_name)
    statement = select(model)
    if hasattr(model, "mission_id"):
        statement = statement.where(model.mission_id == mission_id)
    if astronaut_id and hasattr(model, "astronaut_id"):
        statement = statement.where(model.astronaut_id == astronaut_id)
    if hasattr(model, "is_synthetic"):
        statement = statement.where(model.is_synthetic.is_(True))
    if hasattr(model, "measured_at"):
        statement = statement.order_by(model.measured_at.desc())
    elif hasattr(model, "created_at"):
        statement = statement.order_by(model.created_at.desc())
    with SessionLocal() as db:
        return db.execute(statement.limit(limit)).scalars().all()


def vital_dto(record):
    if isinstance(record, dict):
        metric = str(record.get("metric_code") or record.get("metric") or "").upper()
        value = record.get("normalized_value", record.get("value"))
        unit = record.get("normalized_unit") or record.get("unit") or ""
        quality_value = record.get("quality")
        verify_value = record.get("verification")
        kind = record.get("source_type")
        get = record.get
    else:
        metric = record.metric_code.upper()
        value = record.normalized_value
        unit = record.normalized_unit
        quality_value = record.quality_status
        verify_value = record.verification_status
        kind = record.source_type
        get = lambda name, default=None: getattr(record, name, default)
    if metric in {"SPO2", "SPO₂", "OXYGEN_SATURATION"}:
        metric = "SpO2"
    elif metric in {"HEART_RATE", "HR"}:
        metric = "HR"
    elif metric in {"RESPIRATORY_RATE", "RR"}:
        metric = "RR"
    return {
        "id": str(get("id") or get("event_id") or ""),
        "event_id": str(get("event_id") or get("id") or ""),
        "astronaut_id": get("astronaut_id") or "",
        "metric_code": metric,
        "value": value,
        "unit": unit,
        "baseline": None,
        "source_type": source(kind),
        "is_synthetic": bool(get("is_synthetic")),
        "measured_at": iso(get("measured_at")),
        "received_at": iso(get("received_at") or get("measured_at")),
        "source_device_id": get("source_device_id") or get("device_id"),
        "quality": quality(quality_value),
        "verification": verification(verify_value),
    }


def measurement_rows(store, settings, mission_id, astronaut_id):
    records = [
        item for item in store.list("measurement", mission_id=mission_id)
        if item.get("astronaut_id") == astronaut_id
    ]
    if records:
        return sorted((vital_dto(x) for x in records),
                      key=lambda r: r["measured_at"], reverse=True)
    return [vital_dto(x) for x in read_dev2(
        "VitalSign", mission_id, astronaut_id, settings, limit=300
    )]


def alert_dto(item):
    get = item.get if isinstance(item, dict) else lambda key, default=None: getattr(item, key, default)
    severity = str(get("severity") or "informational").lower()
    if severity == "information":
        severity = "informational"
    if severity not in {"informational", "advisory", "warning", "critical", "data-unavailable"}:
        severity = "informational"
    status = str(get("status") or "OPEN").lower()
    if status not in {"open", "acknowledged", "closed"}:
        status = "open"
    snap = get("rule_snapshot") or {}
    return {
        "id": str(get("id") or get("event_id") or ""),
        "event_id": str(get("event_id") or get("id") or ""),
        "astronaut_id": get("astronaut_id"),
        "title": get("title") or get("message") or "Medical review required",
        "severity": severity,
        "status": status,
        "rule_id": get("rule_id") or snap.get("rule_id"),
        "rule_version": get("rule_version") or snap.get("version"),
        "approval_status": "approved-demo" if str(get("rule_approval_status") or snap.get("approval") or "").upper() in {"APPROVED", "DEMO_ONLY"} else "unapproved",
        "evidence": get("evidence_refs") or ([get("evidence_event_id")] if get("evidence_event_id") else []),
        "created_at": iso(get("created_at") or get("measured_at")),
        "clinician_acknowledged_at": get("clinician_acknowledged_at"),
        "is_synthetic": bool(get("is_synthetic")),
    }


def rows_for_alerts(store, settings, mission_id, astronaut_id):
    records = [
        item for item in store.list("health_alert", mission_id=mission_id)
        if item.get("astronaut_id") in {None, astronaut_id}
    ]
    if records:
        return [alert_dto(x) for x in records]
    return [alert_dto(x) for x in read_dev2(
        "LocalHealthAlert", mission_id, astronaut_id, settings
    )]


@router.get("/missions/{mission_id}/command")
def command(mission_id: str, astronaut_id: str,
            principal=Depends(require("measurements:read")),
            store=Depends(get_store), settings=Depends(get_settings)):
    authorized(principal, mission_id)
    crew_rows = [r for r in store.list("astronauts", mission_id=mission_id)
                 if not r.get("archived")]
    if not crew_rows and settings.environment in {"development", "test"} and mission_id == MISSION:
        from app.models.dev2_models import VitalSign
        from app.core.db import SessionLocal
        with SessionLocal() as db:
            crew_ids = db.execute(select(VitalSign.astronaut_id).where(
                VitalSign.mission_id == mission_id
            ).distinct().limit(20)).scalars().all()
        crew_rows = [{"astronaut_id": crew_id,
                      "display_name": "Synthetic " + crew_id, "is_synthetic": True}
                     for crew_id in crew_ids]
    crew = [{
        "id": r.get("astronaut_id"), "crew_code": r.get("astronaut_id"),
        "display_name": r.get("display_name") or r.get("astronaut_id"),
        "role": "crew", "status": "unverified"
    } for r in crew_rows]
    devices = [r for r in store.list("devices", mission_id=mission_id)
               if not r.get("archived")]
    vitals = measurement_rows(store, settings, mission_id, astronaut_id)[:24]
    alerts = rows_for_alerts(store, settings, mission_id, astronaut_id)
    mission = store.get("missions", mission_id) or {}
    start = mission.get("starts_at")
    day = 0
    if start:
        try:
            day = max(0, (datetime.now(timezone.utc) -
                datetime.fromisoformat(start.replace("Z", "+00:00"))).days + 1)
        except (ValueError, TypeError):
            pass
    return {
        "mission_id": mission_id,
        "mission_phase": mission.get("phase") or "UNVERIFIED",
        "mission_day": day,
        "timestamp": now_iso(),
        "crew": crew, "vitals": vitals, "alerts": alerts,
        "exam_backlog": 0,
        "sync_state": ("pending" if store.pending_count else
                       "connected" if settings.sync_rpc_url and settings.sync_access_token
                       else "offline"),
        "devices_online": sum(str(d.get("status", "")).lower() == "online" for d in devices),
        "devices_total": len(devices),
        "is_synthetic": bool(vitals) and all(r["is_synthetic"] for r in vitals),
    }


@router.get("/measurements/trends")
def trends(astronaut_id: str, mission_id: str = MISSION,
           hours: int = Query(24, ge=1, le=720),
           principal=Depends(require("measurements:read")),
           store=Depends(get_store), settings=Depends(get_settings)):
    authorized(principal, mission_id)
    records = measurement_rows(store, settings, mission_id, astronaut_id)
    if not records:
        return []
    # Historical demo seed is charted at its actual timestamps, not fabricated as live.
    latest = max(datetime.fromisoformat(x["measured_at"].replace("Z", "+00:00"))
                 for x in records if x["measured_at"])
    boundary = latest - timedelta(hours=hours)
    buckets = {}
    for record in records:
        if record["metric_code"] not in {"HR", "SpO2", "RR"}:
            continue
        stamp = record["measured_at"]
        try:
            when = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        except ValueError:
            continue
        if when < boundary:
            continue
        item = buckets.setdefault(stamp, {"timestamp": stamp, "label": stamp[11:16],
                                          "HR": None, "SpO2": None, "RR": None})
        item[record["metric_code"]] = record["value"]
    return sorted(buckets.values(), key=lambda x: x["timestamp"])[-240:]


def domain_dto(record, table):
    get = record.get if isinstance(record, dict) else lambda key, default=None: getattr(record, key, default)
    measured = get("measured_at") or get("created_at")
    key = get("metric_code") or get("assay_code") or get("symptom_code") or get("event_id") or table
    value = next((v for v in (
        get("normalized_value"), get("value"), get("result_value"),
        get("severity"), get("status"), get("raw_value"),
    ) if v is not None), "REVIEW")
    return {
        "id": str(get("id") or get("event_id") or key),
        "label": str(key),
        "value": str(value), "unit": str(get("normalized_unit") or get("unit") or ""),
        "measured_at": iso(measured),
        "source": str(get("source_type") or "UNKNOWN"),
        "quality": verification(get("verification") or get("verification_status")),
        "details": "Historical/synthetic record; human review required",
        "record_table": table,
        "is_synthetic": bool(get("is_synthetic")),
    }


@router.get("/reports/domains/{domain_id}")
def domain_records(domain_id: str, astronaut_id: str, mission_id: str = MISSION,
                   principal=Depends(require("measurements:read")),
                   store=Depends(get_store), settings=Depends(get_settings)):
    authorized(principal, mission_id)
    if domain_id not in DOMAIN_TABLES:
        raise HTTPException(404, "Unknown monitoring domain")
    # Scope the entire sensitive domain; never leak behavioral notes to crew.
    if domain_id == "sleep" and not set(principal.roles).intersection({"admin", "flight_surgeon"}):
        principal.deny("behavioral:restricted", mission_id=mission_id)
    result = []
    for kind in DOMAIN_STORE[domain_id]:
        for item in store.list(kind, mission_id=mission_id):
            if item.get("astronaut_id") not in {None, astronaut_id}:
                continue
            result.append(domain_dto(item, kind))
    if result:
        return result[:120]
    for model in DOMAIN_TABLES[domain_id]:
        for item in read_dev2(model, mission_id, astronaut_id, settings, limit=12):
            result.append(domain_dto(item, item.__tablename__))
    return result[:120]


class Acknowledgment(BaseModel):
    action: Literal["acknowledge"] = "acknowledge"


@router.post("/alerts/{alert_id}/acknowledgments")
def acknowledge(alert_id: str, body: Acknowledgment,
                idempotency_key: str | None = Header(default=None),
                principal=Depends(require("alerts:read")),
                store=Depends(get_store), settings=Depends(get_settings)):
    if not set(principal.roles).intersection({"admin", "flight_surgeon"}):
        principal.deny("alerts:acknowledge")
    existing = store.get("health_alert", alert_id)
    if existing:
        authorized(principal, existing["mission_id"])
        if existing.get("status", "open").lower() != "acknowledged":
            updated = dict(existing, status="acknowledged",
                           clinician_acknowledged_at=now_iso())
            store.put("health_alert", alert_id, updated,
                      mission_id=existing["mission_id"], actor_id=principal.user_id,
                      immutable=False, enqueue=False)
            store.audit("alert.acknowledged", principal.user_id,
                        mission_id=existing["mission_id"], record_id=alert_id)
            existing = updated
        return alert_dto(existing)
    if settings.environment in {"development", "test"}:
        from app.core.db import SessionLocal
        from app.models.dev2_models import LocalHealthAlert
        with SessionLocal.begin() as db:
            row = db.get(LocalHealthAlert, alert_id)
            if row:
                authorized(principal, MISSION)
                if row.status != "ACKNOWLEDGED":
                    row.status = "ACKNOWLEDGED"
                result = alert_dto(row)
        if row:
            store.audit("alert.demo_acknowledged", principal.user_id,
                        mission_id=MISSION, record_id=alert_id)
            return result
    raise HTTPException(404, "Alert not found")


class SymptomInput(BaseModel):
    event_id: str = Field(min_length=1, max_length=128)
    mission_id: str = MISSION
    astronaut_id: str = Field(min_length=1, max_length=128)
    symptom_code: str = Field(min_length=1, max_length=100)
    severity: Literal["mild", "moderate", "serious"]
    notes: str = Field(default="", max_length=500)
    is_synthetic: Literal[True] = True


@router.post("/symptoms", status_code=201)
def submit_symptom(body: SymptomInput,
                   principal=Depends(require("measurements:write")),
                   store=Depends(get_store), settings=Depends(get_settings)):
    authorized(principal, body.mission_id)
    if settings.environment not in {"development", "test"}:
        raise AppError(403, "synthetic_data_disabled",
                       "Synthetic symptom reports are development-only")
    now = now_iso()
    record = {
        "event_id": body.event_id, "mission_id": body.mission_id,
        "astronaut_id": body.astronaut_id, "symptom_code": body.symptom_code,
        "severity": body.severity, "notes": body.notes, "is_synthetic": True,
        "source_type": "SIMULATED", "quality": "VALID",
        "verification": "UNVERIFIED", "measured_at": now, "received_at": now,
        "source_reference": "rocketpulse-frontend", "source_revision": "v1",
    }
    saved = store.put("symptom_report", body.event_id, record,
                      mission_id=body.mission_id, actor_id=principal.user_id)
    if body.severity == "serious":
        from app.incidents.service import ingest_serious_symptom
        ingest_serious_symptom({
            **record, "symptom": body.symptom_code, "onset": now,
            "body_location": "unspecified"
        }, store, settings, principal.user_id)
    return {"event": saved, "persisted_locally": True,
            "cloud_receipt_confirmed": False}


@router.get("/sync/status")
def sync_status(principal=Depends(require("sync:manage")),
                store=Depends(get_store)):
    allowed = None if "*" in principal.mission_ids else principal.mission_ids
    counts = store.queue_status(mission_ids=allowed).get("counts", {})
    queue_depth = sum(counts.get(k, 0) for k in ("pending", "retry", "sending"))
    return {"queue_depth": queue_depth, "last_receipt_at": None,
            "state": "pending" if queue_depth else "idle",
            "counts": counts}

@router.post("/sync/run")
def sync_authorized_mission(
    mission_id: str,
    request: Request,
    principal=Depends(require("sync:manage")),
    store=Depends(get_store),
    settings=Depends(get_settings),
):
    """Manual cloud sync using the request's verified, short-lived user session.

    Requires a server-approved JWT, explicit mission authorization and a
    configured *fixed* Supabase RPC URL. This endpoint does not persist tokens,
    start automatic sync, accept URLs from clients, or expose outbox contents.
    """
    from app.sync.worker import HTTPReceiptTransport, SyncWorker

    authorized(principal, mission_id)
    if not settings.sync_rpc_url or not settings.supabase_anon_key:
        raise AppError(503, "cloud_not_configured",
                       "Cloud synchronization endpoint is not configured")
    # current_principal already verified this Bearer token's signature, issuer,
    # audience and trusted role/mission claims for this request.
    authorization = request.headers.get("authorization") or ""
    if not authorization.lower().startswith("bearer "):
        raise AppError(401, "authentication_required", "Bearer session required")
    bearer = authorization.split(" ", 1)[1].strip()
    # Production cloud auth must be a real Supabase JWT, never an offline grant
    # or locally signed development/test token.
    if principal.offline:
        principal.deny("sync:online_session_required", mission_id=mission_id)
    import jwt
    try:
        signing_algorithm = jwt.get_unverified_header(bearer).get("alg")
    except (jwt.PyJWTError, ValueError):
        raise AppError(401, "invalid_session", "Invalid session")
    if signing_algorithm not in {"RS256", "ES256"}:
        raise AppError(403, "cloud_session_required",
                       "Cloud sync requires a Supabase asymmetric-signed JWT")
    transport = HTTPReceiptTransport(settings)
    transport.access_token = bearer
    # Only kinds implemented by the existing cloud RPC are eligible.
    # Audit, cursor and alert events remain durable locally, never sent as
    # unsupported RPC kinds that would exhaust retries.
    result = SyncWorker(
        store, transport, settings.sync_max_attempts, settings.sync_batch_size
    ).run_once(mission_ids=[mission_id], kinds=[
        "measurement", "vital_sign", "symptom",
        "radiation", "environment", "laboratory_result",
        "examination", "wellness", "report",
    ])
    store.audit(
        "sync.run_user_session", principal.user_id, mission_id=mission_id,
        details={"delivered": result["delivered"], "failed": result["failed"]},
    )
    return result
