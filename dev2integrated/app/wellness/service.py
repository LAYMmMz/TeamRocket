from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.dev1_bridge import ActorContext, Dev1IntegrationBridge
from app.models.dev2_models import (
    BehavioralCheckin,
    FunctionalAssessment,
    GravityTransitionEvent,
    HealthBaseline,
    SleepSession,
    SymptomReport,
    VitalSign,
    new_uuid,
)
from app.schemas.dev2_schemas import (
    BaselineCreate,
    BehavioralCheckinCreate,
    GravityAssessmentCreate,
    SleepSessionCreate,
    SymptomCreate,
    TrendComparisonOut,
)


RESPIRATORY_RED_FLAGS = {"DYSPNEA", "SHORTNESS_OF_BREATH", "CHEST_PAIN", "SYNCOPE", "HYPOXIA_SYMPTOM"}


class WellnessService:
    @staticmethod
    def upsert_baseline(db: Session, payload: BaselineCreate) -> HealthBaseline:
        existing = db.scalars(
            select(HealthBaseline).where(
                HealthBaseline.astronaut_id == payload.astronaut_id,
                HealthBaseline.metric_code == payload.metric_code,
                HealthBaseline.body_region == payload.body_region,
                HealthBaseline.measurement_method == payload.measurement_method,
            )
        ).first()
        if existing:
            existing.baseline_value = payload.baseline_value
            existing.std_dev = payload.std_dev
            existing.unit = payload.unit
            existing.updated_at = datetime.now(timezone.utc)
            db.flush()
            return existing

        row = HealthBaseline(**payload.model_dump())
        db.add(row)
        db.flush()
        return row

    @staticmethod
    def compare_vital_trend(
        db: Session,
        astronaut_id: str,
        metric_code: str,
        window_days: int = 30,
        body_region: str = "WHOLE_BODY",
        measurement_method: str = "STANDARD",
    ) -> TrendComparisonOut:
        baseline = db.scalars(
            select(HealthBaseline).where(
                HealthBaseline.astronaut_id == astronaut_id,
                HealthBaseline.metric_code == metric_code,
                HealthBaseline.body_region == body_region,
                HealthBaseline.measurement_method == measurement_method,
            )
        ).first()

        cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
        vitals = db.scalars(
            select(VitalSign)
            .where(
                VitalSign.astronaut_id == astronaut_id,
                VitalSign.metric_code == metric_code,
                VitalSign.quality_status == "VALID",
                VitalSign.measured_at >= cutoff,
            )
            .order_by(VitalSign.measured_at.asc())
        ).all()

        if not baseline or not vitals:
            return TrendComparisonOut(
                astronaut_id=astronaut_id,
                metric_code=metric_code,
                body_region=body_region,
                measurement_method=measurement_method,
                status="UNAVAILABLE",
                baseline_value=baseline.baseline_value if baseline else None,
                sample_count=len(vitals),
                unit=baseline.unit if baseline else None,
                badge="MISSING_BASELINE_OR_DATA",
            )

        latest = vitals[-1]
        delta = round(latest.normalized_value - baseline.baseline_value, 2)
        pct = round((delta / baseline.baseline_value) * 100.0, 2) if baseline.baseline_value else 0.0
        return TrendComparisonOut(
            astronaut_id=astronaut_id,
            metric_code=metric_code,
            body_region=body_region,
            measurement_method=measurement_method,
            status="AVAILABLE",
            baseline_value=baseline.baseline_value,
            latest_value=latest.normalized_value,
            delta=delta,
            percent_change=pct,
            sample_count=len(vitals),
            unit=baseline.unit,
            badge="SIMULATED" if latest.is_synthetic else "VERIFIED",
        )

    @staticmethod
    def create_symptom_report(db: Session, payload: SymptomCreate) -> Dict[str, Any]:
        event_id = payload.event_id or new_uuid()
        report = SymptomReport(
            event_id=event_id,
            astronaut_id=payload.astronaut_id,
            mission_id=payload.mission_id,
            symptom_code=payload.symptom_code.upper(),
            severity=str(payload.severity),
            onset_at=payload.onset_at,
            measured_at=payload.measured_at,
            received_at=datetime.now(timezone.utc),
            body_location=payload.body_location,
            is_sensitive=payload.is_sensitive,
            notes=payload.notes,
            visibility_classification="PRIVATE_CLINICAL" if payload.is_sensitive else "CLINICAL_TEAM",
            source_type=payload.source_type,
            is_synthetic=payload.is_synthetic,
            quality_status=payload.quality_status,
            verification_status=payload.verification_status,
        )
        db.add(report)
        db.flush()

        Dev1IntegrationBridge.enqueue_sync(
            db=db,
            event_id=event_id,
            resource_type="symptom_reports",
            priority=1 if payload.severity >= 7.0 else 3,
            payload={"id": report.id, "symptom_code": report.symptom_code, "severity": payload.severity},
        )

        incident_id = None
        # Task 10 & S03: Serious respiratory/cardiac symptom triggers immediate local incident even without sensor data
        if report.symptom_code in RESPIRATORY_RED_FLAGS and payload.severity >= 7.0:
            recent_spo2 = db.scalars(
                select(VitalSign)
                .where(
                    VitalSign.astronaut_id == payload.astronaut_id,
                    VitalSign.metric_code == "SPO2",
                    VitalSign.quality_status == "VALID",
                )
                .order_by(VitalSign.measured_at.desc())
            ).first()

            evidence = [f"symptom_reports:{report.id}"]
            if not recent_spo2:
                # Explicitly emit DATA_UNAVAILABLE badge rather than fabricating SpO2
                Dev1IntegrationBridge.emit_alert_and_optional_incident(
                    db=db,
                    rule_id="RULE-SPO2-MISSING-COVERAGE",
                    rule_version="1.0.0",
                    rule_approval_status="APPROVED",
                    severity="DATA_UNAVAILABLE",
                    title="SpO2 sensor telemetry unavailable during acute respiratory symptom report",
                    evidence_refs=evidence,
                    astronaut_id=payload.astronaut_id,
                    open_incident=False,
                    is_synthetic=payload.is_synthetic,
                )

            res = Dev1IntegrationBridge.emit_alert_and_optional_incident(
                db=db,
                rule_id="RULE-ACUTE-SYMPTOM-ESCALATION",
                rule_version="1.0.0",
                rule_approval_status="APPROVED",
                severity="CRITICAL",
                title=f"Critical symptom reported: {report.symptom_code} (severity {payload.severity}/10)",
                evidence_refs=evidence,
                astronaut_id=payload.astronaut_id,
                open_incident=True,
                incident_type="ACUTE_CLINICAL_SYMPTOM",
                is_synthetic=payload.is_synthetic,
            )
            incident_id = res["incident_id"]

        # Task 16 & S04: Correlate headache with active 1-hour elevated CO2 window without asserting causation
        if report.symptom_code == "HEADACHE" and payload.severity >= 4.0:
            res = Dev1IntegrationBridge.emit_alert_and_optional_incident(
                db=db,
                rule_id="RULE-SYMPTOM-CORRELATION-REVIEW",
                rule_version="1.0.0",
                rule_approval_status="DEMO_ONLY",
                severity="ADVISORY",
                title=f"Crew headache reported ({payload.severity}/10) — review alongside habitat logs",
                evidence_refs=[f"symptom_reports:{report.id}"],
                astronaut_id=payload.astronaut_id,
                open_incident=True,
                incident_type="CO2_AND_HEADACHE_CORRELATED_REVIEW",
                is_synthetic=payload.is_synthetic,
            )
            incident_id = res["incident_id"]

        return {
            "id": report.id,
            "event_id": report.event_id,
            "symptom_code": report.symptom_code,
            "severity": payload.severity,
            "incident_triggered": incident_id is not None,
            "incident_id": incident_id,
            "is_synthetic": report.is_synthetic,
        }

    @staticmethod
    def record_gravity_transition(
        db: Session,
        mission_id: str,
        from_g: float,
        to_g: float,
        occurred_at: datetime,
        astronaut_ids: List[str],
    ) -> Dict[str, Any]:
        settings = get_settings()
        event = GravityTransitionEvent(
            mission_id=mission_id,
            from_g=from_g,
            to_g=to_g,
            occurred_at=occurred_at,
            measured_at=occurred_at,
            received_at=datetime.now(timezone.utc),
            source_type="SIMULATED",
            is_synthetic=True,
            verification_status="RESEARCH_ONLY",
        )
        db.add(event)
        db.flush()

        opened_assessments = []
        for astro_id in astronaut_ids:
            assessment = FunctionalAssessment(
                astronaut_id=astro_id,
                gravity_event_id=event.id,
                symptom_score=0.0,
                reaction_time_ms=0.0,
                within_research_bounds=False,
                eva_clearance_status="PENDING_HUMAN_REVIEW",
                parameter_classification="RESEARCH_ONLY",
                quality_status="UNVERIFIED",
                verification_status="RESEARCH_ONLY",
            )
            db.add(assessment)
            db.flush()
            opened_assessments.append(assessment.id)

        return {
            "gravity_event_id": event.id,
            "from_g": from_g,
            "to_g": to_g,
            "adaptation_window_hours": settings.gravity_adaptation_window_hours,
            "parameter_classification": "RESEARCH_ONLY",
            "eva_clearance_status": "PENDING_HUMAN_REVIEW",
            "opened_assessment_ids": opened_assessments,
        }

    @staticmethod
    def submit_gravity_assessment(db: Session, payload: GravityAssessmentCreate) -> Dict[str, Any]:
        settings = get_settings()
        within_bounds = (
            payload.symptom_score <= settings.gravity_symptom_cutoff
            and payload.reaction_time_ms < settings.gravity_reaction_time_cutoff_ms
        )
        # Task 17: Configurable research criteria ONLY; never autonomously grant or deny EVA clearance
        assessment = FunctionalAssessment(
            event_id=payload.event_id or new_uuid(),
            astronaut_id=payload.astronaut_id,
            gravity_event_id=payload.gravity_event_id,
            symptom_score=payload.symptom_score,
            reaction_time_ms=payload.reaction_time_ms,
            within_research_bounds=within_bounds,
            eva_clearance_status="PENDING_HUMAN_REVIEW",
            parameter_classification="RESEARCH_ONLY",
            assessed_at=payload.assessed_at,
            measured_at=payload.measured_at,
            source_type=payload.source_type,
            is_synthetic=payload.is_synthetic,
            verification_status="RESEARCH_ONLY",
        )
        db.add(assessment)
        db.flush()

        if not within_bounds:
            Dev1IntegrationBridge.emit_alert_and_optional_incident(
                db=db,
                rule_id="RULE-GRAVITY-ADAPTATION-REVIEW",
                rule_version="1.0.0",
                rule_approval_status="RESEARCH_ONLY",
                severity="ADVISORY",
                title="Gravity adaptation research threshold exceeded — flight surgeon review required",
                evidence_refs=[f"functional_assessments:{assessment.id}"],
                astronaut_id=payload.astronaut_id,
                open_incident=False,
                is_synthetic=payload.is_synthetic,
            )

        return {
            "id": assessment.id,
            "astronaut_id": assessment.astronaut_id,
            "within_research_bounds": within_bounds,
            "research_thresholds": {
                "window_hours": settings.gravity_adaptation_window_hours,
                "max_symptom_score": settings.gravity_symptom_cutoff,
                "max_reaction_time_ms": settings.gravity_reaction_time_cutoff_ms,
                "classification": "RESEARCH_ONLY",
            },
            "eva_clearance_status": "PENDING_HUMAN_REVIEW",
        }

    @staticmethod
    def log_sleep_session(db: Session, payload: SleepSessionCreate) -> SleepSession:
        row = SleepSession(
            event_id=payload.event_id or new_uuid(),
            astronaut_id=payload.astronaut_id,
            start_at=payload.start_at,
            end_at=payload.end_at,
            duration_minutes=int(round(payload.duration_hours * 60)),
            duration_hours=payload.duration_hours,
            awakenings_count=payload.awakenings_count,
            measured_at=payload.measured_at,
            source_type=payload.source_type,
            is_synthetic=payload.is_synthetic,
            quality_status=payload.quality_status,
            verification_status=payload.verification_status,
        )
        db.add(row)
        db.flush()
        return row

    @staticmethod
    def create_behavioral_checkin(db: Session, payload: BehavioralCheckinCreate) -> Dict[str, Any]:
        severe_distress = payload.mood_score <= 2.0 or payload.stress_score >= 9.0 or payload.fatigue_score >= 9.0
        row = BehavioralCheckin(
            event_id=payload.event_id or new_uuid(),
            astronaut_id=payload.astronaut_id,
            assessment_type=payload.assessment_type,
            score=payload.mood_score,
            mood_score=payload.mood_score,
            fatigue_score=payload.fatigue_score,
            stress_score=payload.stress_score,
            visibility_classification=payload.visibility_classification,
            confidential_notes=payload.confidential_notes,
            confidential_escalation_triggered=severe_distress,
            measured_at=payload.measured_at,
            source_type=payload.source_type,
            is_synthetic=payload.is_synthetic,
            quality_status=payload.quality_status,
            verification_status=payload.verification_status,
        )
        db.add(row)
        db.flush()

        if severe_distress:
            Dev1IntegrationBridge.emit_alert_and_optional_incident(
                db=db,
                rule_id="RULE-CONFIDENTIAL-BEHAVIORAL-ESCALATION",
                rule_version="1.0.0",
                rule_approval_status="APPROVED",
                severity="WARNING",
                title="Confidential behavioral-health review requested (restricted clinical channel)",
                evidence_refs=[f"behavioral_checkins:{row.id}"],
                astronaut_id=payload.astronaut_id,
                open_incident=False,
                is_synthetic=payload.is_synthetic,
            )

        return {
            "id": row.id,
            "astronaut_id": row.astronaut_id,
            "visibility_classification": row.visibility_classification,
            "confidential_escalation_triggered": severe_distress,
        }

    @staticmethod
    def get_wellness_summary(db: Session, astronaut_id: str, actor: ActorContext) -> Dict[str, Any]:
        Dev1IntegrationBridge.enforce_behavioral_privacy(
            db=db,
            actor=actor,
            target_astronaut_id=astronaut_id,
            visibility_classification="PRIVATE_CLINICAL",
        )
        Dev1IntegrationBridge.record_audit(
            db=db,
            actor=actor,
            action="READ_WELLNESS_SUMMARY",
            resource_type="behavioral_checkins",
            resource_id=astronaut_id,
            outcome="ALLOWED",
        )

        latest_sleep = db.scalars(
            select(SleepSession)
            .where(SleepSession.astronaut_id == astronaut_id)
            .order_by(SleepSession.end_at.desc())
        ).first()

        sleep_status = "AVAILABLE"
        latest_sleep_hours = None
        if not latest_sleep:
            sleep_status = "MISSING"
        else:
            latest_sleep_hours = (
                latest_sleep.duration_hours
                if latest_sleep.duration_hours is not None
                else round(latest_sleep.duration_minutes / 60.0, 2)
            )
            if (datetime.now(timezone.utc) - latest_sleep.end_at.replace(tzinfo=timezone.utc)).total_seconds() > 36 * 3600:
                sleep_status = "STALE_MISSING"

        checkins = db.scalars(
            select(BehavioralCheckin)
            .where(BehavioralCheckin.astronaut_id == astronaut_id)
            .order_by(BehavioralCheckin.measured_at.desc())
            .limit(10)
        ).all()

        return {
            "astronaut_id": astronaut_id,
            "sleep_status": sleep_status,
            "latest_sleep_hours": latest_sleep_hours,
            "iss_historical_context_note": "6.0-6.5h ISS average is historical context only, not a clinical target.",
            "behavioral_checkins": [
                {
                    "id": c.id,
                    "measured_at": c.measured_at.isoformat(),
                    "mood_score": c.mood_score,
                    "fatigue_score": c.fatigue_score,
                    "stress_score": c.stress_score,
                    "visibility_classification": c.visibility_classification,
                    "confidential_notes": c.confidential_notes,
                    "is_synthetic": c.is_synthetic,
                }
                for c in checkins
            ],
        }