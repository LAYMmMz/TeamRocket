from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Tuple
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dev1_bridge import Dev1IntegrationBridge
from app.models.dev2_models import ExerciseSession, VitalSign, new_uuid
from app.schemas.dev2_schemas import ExerciseSessionCreate, VitalCreate, VitalOut


UNIT_NORMALIZERS: Dict[str, Dict[str, Tuple[str, float, float]]] = {
    "HR": {"bpm": ("bpm", 1.0, 0.0)},
    "SPO2": {"%": ("%", 1.0, 0.0)},
    "RR": {"breaths/min": ("breaths/min", 1.0, 0.0), "rpm": ("breaths/min", 1.0, 0.0)},
    "BP_SYS": {"mmHg": ("mmHg", 1.0, 0.0)},
    "BP_DIA": {"mmHg": ("mmHg", 1.0, 0.0)},
    "TEMP": {
        "C": ("C", 1.0, 0.0),
        "F": ("C", 5.0 / 9.0, -32.0 * 5.0 / 9.0),
    },
}


class VitalsService:
    @staticmethod
    def _normalize_unit(metric_code: str, value: float, unit: str) -> Tuple[float, str]:
        allowed = UNIT_NORMALIZERS.get(metric_code, {})
        if unit not in allowed:
            raise HTTPException(
                status_code=422,
                detail=f"Incompatible unit '{unit}' for metric '{metric_code}'.",
            )
        target_unit, factor, offset = allowed[unit]
        return round((value * factor) + offset, 3), target_unit

    @staticmethod
    def _resolve_activity_context(db: Session, astronaut_id: str, measured_at: datetime, explicit: str | None) -> str:
        if explicit:
            return explicit
        recovery_buffer = timedelta(minutes=20)
        sessions = db.scalars(
            select(ExerciseSession).where(ExerciseSession.astronaut_id == astronaut_id)
        ).all()
        m_utc = measured_at if measured_at.tzinfo else measured_at.replace(tzinfo=timezone.utc)
        for s in sessions:
            s_start = s.started_at if s.started_at.tzinfo else s.started_at.replace(tzinfo=timezone.utc)
            s_end = s.ended_at if s.ended_at.tzinfo else s.ended_at.replace(tzinfo=timezone.utc)
            if s_start <= m_utc <= s_end:
                return "EXERCISE_ACTIVE"
            if s_end < m_utc <= (s_end + recovery_buffer):
                return "POST_EXERCISE"
        return "RESTING"

    @staticmethod
    def ingest_vital(db: Session, payload: VitalCreate) -> VitalOut:
        event_id = payload.event_id or new_uuid()
        existing = db.scalars(select(VitalSign).where(VitalSign.event_id == event_id)).first()
        if existing:
            return VitalOut(
                id=existing.id,
                event_id=existing.event_id,
                astronaut_id=existing.astronaut_id,
                metric_code=existing.metric_code,
                raw_value=existing.raw_value,
                raw_unit=existing.raw_unit,
                normalized_value=existing.normalized_value,
                normalized_unit=existing.normalized_unit,
                activity_context=existing.activity_context,
                quality_status=existing.quality_status,
                verification_status=existing.verification_status,
                source_type=existing.source_type,
                is_synthetic=existing.is_synthetic,
                measured_at=existing.measured_at,
                received_at=existing.received_at,
            )

        norm_val, norm_unit = VitalsService._normalize_unit(payload.metric_code, payload.value, payload.unit)
        context = VitalsService._resolve_activity_context(
            db, payload.astronaut_id, payload.measured_at, payload.activity_context
        )

        vital = VitalSign(
            event_id=event_id,
            astronaut_id=payload.astronaut_id,
            mission_id=payload.mission_id,
            metric_code=payload.metric_code,
            raw_value=payload.value,
            raw_unit=payload.unit,
            normalized_value=norm_val,
            normalized_unit=norm_unit,
            activity_context=context,
            source_type=payload.source_type,
            is_synthetic=payload.is_synthetic,
            measured_at=payload.measured_at,
            received_at=datetime.now(timezone.utc),
            quality_status=payload.quality_status,
            verification_status=payload.verification_status,
            source_device_id=payload.source_device_id,
        )
        db.add(vital)
        db.flush()

        alert_id = None
        if payload.quality_status == "VALID":
            # Task 14 & S02: Elevated HR during exercise is contextualized, NOT flagged as resting abnormality
            if payload.metric_code == "HR" and norm_val > 110.0 and context == "RESTING":
                res = Dev1IntegrationBridge.emit_alert_and_optional_incident(
                    db=db,
                    rule_id="RULE-RESTING-HR-ELEVATED",
                    rule_version="1.0.0",
                    rule_approval_status="DEMO_ONLY",
                    severity="ADVISORY",
                    title=f"Resting HR elevated ({norm_val} bpm) without logged exercise context",
                    evidence_refs=[f"vital_signs:{vital.id}"],
                    astronaut_id=payload.astronaut_id,
                    open_incident=False,
                    is_synthetic=payload.is_synthetic,
                )
                alert_id = res["alert_id"]
            elif payload.metric_code == "SPO2" and norm_val < 92.0:
                res = Dev1IntegrationBridge.emit_alert_and_optional_incident(
                    db=db,
                    rule_id="RULE-LOW-SPO2-WARNING",
                    rule_version="1.0.0",
                    rule_approval_status="APPROVED",
                    severity="CRITICAL",
                    title=f"Low SpO2 detected ({norm_val}%)",
                    evidence_refs=[f"vital_signs:{vital.id}"],
                    astronaut_id=payload.astronaut_id,
                    open_incident=True,
                    incident_type="HYPOXIA_RISK",
                    is_synthetic=payload.is_synthetic,
                )
                alert_id = res["alert_id"]

        Dev1IntegrationBridge.enqueue_sync(
            db=db,
            event_id=event_id,
            resource_type="vital_signs",
            priority=1 if alert_id else 5,
            payload={"id": vital.id, "metric_code": vital.metric_code, "value": norm_val},
        )

        return VitalOut(
            id=vital.id,
            event_id=vital.event_id,
            astronaut_id=vital.astronaut_id,
            metric_code=vital.metric_code,
            raw_value=vital.raw_value,
            raw_unit=vital.raw_unit,
            normalized_value=vital.normalized_value,
            normalized_unit=vital.normalized_unit,
            activity_context=vital.activity_context,
            quality_status=vital.quality_status,
            verification_status=vital.verification_status,
            source_type=vital.source_type,
            is_synthetic=vital.is_synthetic,
            measured_at=vital.measured_at,
            received_at=vital.received_at,
            alert_generated=alert_id,
        )

    @staticmethod
    def get_latest_vitals(db: Session, astronaut_id: str, stale_after_minutes: int = 120) -> Dict[str, Any]:
        metrics = ["HR", "SPO2", "RR", "BP_SYS", "BP_DIA", "TEMP"]
        now = datetime.now(timezone.utc)
        summary: Dict[str, Any] = {}

        for m in metrics:
            latest = db.scalars(
                select(VitalSign)
                .where(VitalSign.astronaut_id == astronaut_id, VitalSign.metric_code == m)
                .order_by(VitalSign.measured_at.desc())
            ).first()
            if not latest:
                summary[m] = {"status": "DATA_UNAVAILABLE", "value": None, "badge": "MISSING"}
                continue

            m_time = latest.measured_at if latest.measured_at.tzinfo else latest.measured_at.replace(tzinfo=timezone.utc)
            is_stale = (now - m_time) > timedelta(minutes=stale_after_minutes) or latest.quality_status == "STALE"
            summary[m] = {
                "id": latest.id,
                "status": "STALE" if is_stale else latest.quality_status,
                "value": latest.normalized_value,
                "unit": latest.normalized_unit,
                "activity_context": latest.activity_context,
                "measured_at": latest.measured_at.isoformat(),
                "badge": "SIMULATED" if latest.is_synthetic else "VERIFIED",
            }
        return {"astronaut_id": astronaut_id, "vitals": summary}

    @staticmethod
    def log_exercise_session(db: Session, payload: ExerciseSessionCreate) -> ExerciseSession:
        # Task 19: Logged exercise contextualizes HR; never infers formal VO2/strength fitness score
        session = ExerciseSession(
            event_id=payload.event_id or new_uuid(),
            astronaut_id=payload.astronaut_id,
            mission_id=payload.mission_id,
            exercise_type=payload.exercise_type,
            started_at=payload.started_at,
            ended_at=payload.ended_at,
            duration_minutes=payload.duration_minutes,
            workload_watts=payload.workload_watts,
            repetitions=payload.repetitions,
            measured_at=payload.measured_at,
            source_type=payload.source_type,
            is_synthetic=payload.is_synthetic,
            quality_status=payload.quality_status,
            verification_status=payload.verification_status,
        )
        db.add(session)
        db.flush()
        return session