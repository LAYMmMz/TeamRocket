from __future__ import annotations

from datetime import datetime, timezone
import uuid
from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def new_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


# --- Bridge & Audit Tables ---
class LocalAuditLog(Base):
    __tablename__ = "local_audit_logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    actor_id: Mapped[str] = mapped_column(String(128))
    actor_role: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(128))
    resource_type: Mapped[str] = mapped_column(String(128))
    resource_id: Mapped[str] = mapped_column(String(128))
    outcome: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class LocalHealthAlert(Base):
    __tablename__ = "local_health_alerts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    incident_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    astronaut_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    location_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    rule_id: Mapped[str] = mapped_column(String(128))
    rule_version: Mapped[str] = mapped_column(String(64))
    rule_approval_status: Mapped[str] = mapped_column(String(64))
    severity: Mapped[str] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(String(512))
    evidence_refs: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(32), default="OPEN")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class LocalMedicalIncident(Base):
    __tablename__ = "local_medical_incidents"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    astronaut_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    location_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    incident_type: Mapped[str] = mapped_column(String(128))
    priority: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="OPEN")
    linked_evidence: Mapped[list] = mapped_column(JSON, default=list)
    causality_asserted: Mapped[bool] = mapped_column(Boolean, default=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class LocalSyncQueueItem(Base):
    __tablename__ = "local_sync_queue"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    event_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    resource_type: Mapped[str] = mapped_column(String(128))
    priority: Mapped[int] = mapped_column(Integer, default=5)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="QUEUED")
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    cloud_receipt_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# --- T09 & T10 & T14: Vitals, ECG, Baselines & Symptoms ---
class VitalSign(Base):
    __tablename__ = "vital_signs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    event_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    astronaut_id: Mapped[str] = mapped_column(String(128), index=True)
    mission_id: Mapped[str] = mapped_column(String(128), default="DEMO-01")
    metric_code: Mapped[str] = mapped_column(String(64), index=True)
    raw_value: Mapped[float] = mapped_column(Float)
    raw_unit: Mapped[str] = mapped_column(String(32))
    normalized_value: Mapped[float] = mapped_column(Float)
    normalized_unit: Mapped[str] = mapped_column(String(32))
    activity_context: Mapped[str] = mapped_column(String(64), default="RESTING")
    source_type: Mapped[str] = mapped_column(String(32), default="SIMULATED")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    quality_status: Mapped[str] = mapped_column(String(32), default="VALID")
    verification_status: Mapped[str] = mapped_column(String(32), default="UNVERIFIED")
    source_device_id: Mapped[str | None] = mapped_column(String(128), nullable=True)


class EcgRecord(Base):
    __tablename__ = "ecg_records"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    event_id: Mapped[str] = mapped_column(String(128), unique=True)
    astronaut_id: Mapped[str] = mapped_column(String(128), index=True)
    mission_id: Mapped[str] = mapped_column(String(128), default="DEMO-01")
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    waveform_reference: Mapped[str] = mapped_column(String(512))
    reviewed_interpretation: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewer_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_type: Mapped[str] = mapped_column(String(32), default="SIMULATED")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    quality_status: Mapped[str] = mapped_column(String(32), default="VALID")
    verification_status: Mapped[str] = mapped_column(String(32), default="UNVERIFIED")


class HealthBaseline(Base):
    __tablename__ = "health_baselines"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    astronaut_id: Mapped[str] = mapped_column(String(128), index=True)
    metric_code: Mapped[str] = mapped_column(String(64), index=True)
    body_region: Mapped[str] = mapped_column(String(64), default="WHOLE_BODY")
    baseline_value: Mapped[float] = mapped_column(Float)
    std_dev: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(32))
    measurement_method: Mapped[str] = mapped_column(String(128), default="PREFLIGHT_MEAN")
    sample_count: Mapped[int] = mapped_column(Integer, default=1)
    validity: Mapped[str] = mapped_column(String(32), default="VALID")
    source_type: Mapped[str] = mapped_column(String(32), default="SIMULATED")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    recalculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SymptomReport(Base):
    __tablename__ = "symptom_reports"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    event_id: Mapped[str] = mapped_column(String(128), unique=True, default=new_uuid)
    astronaut_id: Mapped[str] = mapped_column(String(128), index=True)
    mission_id: Mapped[str] = mapped_column(String(128), default="DEMO-01")
    symptom_code: Mapped[str] = mapped_column(String(128))
    severity: Mapped[str] = mapped_column(String(32))
    onset_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    body_location: Mapped[str] = mapped_column(String(128))
    is_sensitive: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    visibility_classification: Mapped[str] = mapped_column(String(64), default="CLINICAL_TEAM")
    source_type: Mapped[str] = mapped_column(String(32), default="SIMULATED")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    quality_status: Mapped[str] = mapped_column(String(32), default="VALID")
    verification_status: Mapped[str] = mapped_column(String(32), default="UNVERIFIED")


class ExerciseSession(Base):
    __tablename__ = "exercise_sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    event_id: Mapped[str] = mapped_column(String(128), unique=True)
    astronaut_id: Mapped[str] = mapped_column(String(128), index=True)
    mission_id: Mapped[str] = mapped_column(String(128), default="DEMO-01")
    exercise_type: Mapped[str] = mapped_column(String(64))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_minutes: Mapped[int] = mapped_column(Integer)
    workload_watts: Mapped[float | None] = mapped_column(Float, nullable=True)
    repetitions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source_type: Mapped[str] = mapped_column(String(32), default="SIMULATED")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    quality_status: Mapped[str] = mapped_column(String(32), default="VALID")
    verification_status: Mapped[str] = mapped_column(String(32), default="UNVERIFIED")


# --- T15 & T16: Radiation, Area Records & Mission Locations ---
class MissionLocation(Base):
    __tablename__ = "mission_locations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    location_code: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    mission_id: Mapped[str] = mapped_column(String(128), default="DEMO-01")
    zone_name: Mapped[str] = mapped_column(String(128))
    location_type: Mapped[str] = mapped_column(String(64))
    is_spe_shelter: Mapped[bool] = mapped_column(Boolean, default=False)
    shielding_notes: Mapped[str] = mapped_column(String(256), default="UNVERIFIED_REFERENCE_ONLY")


class RadiationAreaRecord(Base):
    __tablename__ = "radiation_area_records"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    event_id: Mapped[str] = mapped_column(String(128), unique=True)
    location_id: Mapped[str] = mapped_column(String(128), index=True)
    sensor_id: Mapped[str] = mapped_column(String(128))
    radiation_metric: Mapped[str] = mapped_column(String(64))
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(32))
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    source_type: Mapped[str] = mapped_column(String(32), default="SIMULATED")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    quality_status: Mapped[str] = mapped_column(String(32), default="VALID")


class PersonalDoseRecord(Base):
    __tablename__ = "personal_dose_records"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    event_id: Mapped[str] = mapped_column(String(128), unique=True)
    astronaut_id: Mapped[str] = mapped_column(String(128), index=True)
    mission_id: Mapped[str] = mapped_column(String(128), default="DEMO-01")
    dosimeter_id: Mapped[str] = mapped_column(String(128))
    dose_quantity: Mapped[str] = mapped_column(String(64))
    particle_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    spectrum_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    raw_value: Mapped[float] = mapped_column(Float)
    raw_unit: Mapped[str] = mapped_column(String(32))
    normalized_value: Mapped[float] = mapped_column(Float)
    normalized_unit: Mapped[str] = mapped_column(String(32))
    interval_hours: Mapped[float] = mapped_column(Float, default=24.0)
    location_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source_type: Mapped[str] = mapped_column(String(32), default="SIMULATED")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    quality_status: Mapped[str] = mapped_column(String(32), default="VALID")
    verification_status: Mapped[str] = mapped_column(String(32), default="UNVERIFIED")


class RadiationEvent(Base):
    __tablename__ = "radiation_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    event_id: Mapped[str] = mapped_column(String(128), unique=True)
    mission_id: Mapped[str] = mapped_column(String(128), default="DEMO-01")
    event_type: Mapped[str] = mapped_column(String(64))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    shelter_location_id: Mapped[str] = mapped_column(String(128))
    rule_approval_state: Mapped[str] = mapped_column(String(64), default="DEMO_ONLY")
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source_type: Mapped[str] = mapped_column(String(32), default="SIMULATED")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    verification_status: Mapped[str] = mapped_column(String(32), default="DEMO_ONLY")


class EnvironmentalReading(Base):
    __tablename__ = "environmental_readings"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    event_id: Mapped[str] = mapped_column(String(128), unique=True)
    location_id: Mapped[str] = mapped_column(String(128), index=True)
    metric_code: Mapped[str] = mapped_column(String(64), index=True)
    raw_value: Mapped[float] = mapped_column(Float)
    raw_unit: Mapped[str] = mapped_column(String(32))
    normalized_value: Mapped[float] = mapped_column(Float)
    normalized_unit: Mapped[str] = mapped_column(String(32))
    averaging_window_minutes: Mapped[int] = mapped_column(Integer, default=60)
    weighting_or_spectrum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    calibration_state: Mapped[str] = mapped_column(String(32), default="CALIBRATED")
    rule_approval_state: Mapped[str] = mapped_column(String(64), default="DEMO_ONLY")
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source_type: Mapped[str] = mapped_column(String(32), default="SIMULATED")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    quality_status: Mapped[str] = mapped_column(String(32), default="VALID")
    verification_status: Mapped[str] = mapped_column(String(32), default="DEMO_ONLY")


class EnvironmentalSample(Base):
    __tablename__ = "environmental_samples"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    event_id: Mapped[str] = mapped_column(String(128), unique=True)
    location_id: Mapped[str] = mapped_column(String(128))
    sample_type: Mapped[str] = mapped_column(String(64))
    sampling_method: Mapped[str] = mapped_column(String(128))
    sample_quantity: Mapped[float] = mapped_column(Float)
    sample_unit: Mapped[str] = mapped_column(String(32))
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source_type: Mapped[str] = mapped_column(String(32), default="SIMULATED")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)


class EnvironmentalLabResult(Base):
    __tablename__ = "environmental_lab_results"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    event_id: Mapped[str] = mapped_column(String(128), unique=True)
    sample_id: Mapped[str] = mapped_column(String(36))
    test_code: Mapped[str] = mapped_column(String(64))
    result_value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(32))
    standard_revision: Mapped[str] = mapped_column(String(64))
    rule_approval_state: Mapped[str] = mapped_column(String(64))
    remediation_required: Mapped[bool] = mapped_column(Boolean, default=False)
    remediation_action: Mapped[str | None] = mapped_column(String(256), nullable=True)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source_type: Mapped[str] = mapped_column(String(32), default="SIMULATED")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    verification_status: Mapped[str] = mapped_column(String(32), default="DEMO_ONLY")


# --- T17 & T18: Gravity, Hydration, Sleep, Nutrition & Behavioral ---
class GravityTransitionEvent(Base):
    __tablename__ = "gravity_transition_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    event_id: Mapped[str] = mapped_column(String(128), unique=True, default=new_uuid)
    mission_id: Mapped[str] = mapped_column(String(128), default="DEMO-01")
    from_g: Mapped[float] = mapped_column(Float)
    to_g: Mapped[float] = mapped_column(Float)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    adaptation_window_hours: Mapped[int] = mapped_column(Integer, default=72)
    parameter_classification: Mapped[str] = mapped_column(String(64), default="RESEARCH_ONLY")
    eva_clearance_status: Mapped[str] = mapped_column(String(64), default="PENDING_HUMAN_REVIEW")
    source_type: Mapped[str] = mapped_column(String(32), default="SIMULATED")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    verification_status: Mapped[str] = mapped_column(String(32), default="RESEARCH_ONLY")


class FunctionalAssessment(Base):
    __tablename__ = "functional_assessments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    event_id: Mapped[str] = mapped_column(String(128), unique=True, default=new_uuid)
    astronaut_id: Mapped[str] = mapped_column(String(128), index=True)
    gravity_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    transition_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    test_type: Mapped[str] = mapped_column(String(64), default="GRAVITY_ADAPTATION")
    symptom_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    symptom_score_10: Mapped[float | None] = mapped_column(Float, nullable=True)
    reaction_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    within_research_bounds: Mapped[bool] = mapped_column(Boolean, default=False)
    research_threshold_exceeded: Mapped[bool] = mapped_column(Boolean, default=False)
    eva_clearance_status: Mapped[str] = mapped_column(String(64), default="PENDING_HUMAN_REVIEW")
    parameter_classification: Mapped[str] = mapped_column(String(64), default="RESEARCH_ONLY")
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    source_type: Mapped[str] = mapped_column(String(32), default="SIMULATED")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    quality_status: Mapped[str] = mapped_column(String(32), default="VALID")
    verification_status: Mapped[str] = mapped_column(String(32), default="RESEARCH_ONLY")


class FluidBalanceLog(Base):
    __tablename__ = "fluid_balance_logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    event_id: Mapped[str] = mapped_column(String(128), unique=True)
    astronaut_id: Mapped[str] = mapped_column(String(128), index=True)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    intake_ml: Mapped[float] = mapped_column(Float)
    output_ml: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(16), default="mL")
    source_type: Mapped[str] = mapped_column(String(32), default="SIMULATED")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)


class SleepSession(Base):
    __tablename__ = "sleep_sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    event_id: Mapped[str] = mapped_column(String(128), unique=True, default=new_uuid)
    astronaut_id: Mapped[str] = mapped_column(String(128), index=True)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_minutes: Mapped[int] = mapped_column(Integer, default=0)
    duration_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    awakenings_count: Mapped[int] = mapped_column(Integer, default=0)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    quality_status: Mapped[str] = mapped_column(String(32), default="VALID")
    verification_status: Mapped[str] = mapped_column(String(32), default="UNVERIFIED")
    source_type: Mapped[str] = mapped_column(String(32), default="SIMULATED")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)


class BehavioralCheckin(Base):
    __tablename__ = "behavioral_checkins"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    event_id: Mapped[str] = mapped_column(String(128), unique=True, default=new_uuid)
    astronaut_id: Mapped[str] = mapped_column(String(128), index=True)
    assessment_type: Mapped[str] = mapped_column(String(64), default="DAILY_CHECKIN")
    score: Mapped[float] = mapped_column(Float, default=0.0)
    mood_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    fatigue_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    stress_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    visibility_classification: Mapped[str] = mapped_column(String(64), default="PRIVATE_CLINICAL")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidential_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidential_escalation_triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    source_type: Mapped[str] = mapped_column(String(32), default="SIMULATED")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    quality_status: Mapped[str] = mapped_column(String(32), default="VALID")
    verification_status: Mapped[str] = mapped_column(String(32), default="UNVERIFIED")


# --- T20, T21, T22, T23, T24: Examinations & Laboratory ---
class MedicalExamSchedule(Base):
    __tablename__ = "medical_exam_schedule"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    astronaut_id: Mapped[str] = mapped_column(String(128), index=True)
    exam_type: Mapped[str] = mapped_column(String(64))
    schedule_source: Mapped[str] = mapped_column(String(128))
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completion_status: Mapped[str] = mapped_column(String(32), default="SCHEDULED")
    result_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)


class VascularUltrasoundResult(Base):
    __tablename__ = "vascular_ultrasound_results"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    event_id: Mapped[str] = mapped_column(String(128), unique=True)
    astronaut_id: Mapped[str] = mapped_column(String(128), index=True)
    vein: Mapped[str] = mapped_column(String(64))
    side: Mapped[str] = mapped_column(String(16))
    flow_pattern: Mapped[str] = mapped_column(String(64))
    thrombus_finding: Mapped[str] = mapped_column(String(64))
    reviewed_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source_type: Mapped[str] = mapped_column(String(32), default="SIMULATED")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    verification_status: Mapped[str] = mapped_column(String(32), default="UNREVIEWED")


class OcularAssessment(Base):
    __tablename__ = "ocular_assessments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    event_id: Mapped[str] = mapped_column(String(128), unique=True)
    astronaut_id: Mapped[str] = mapped_column(String(128), index=True)
    test_type: Mapped[str] = mapped_column(String(64))
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    report_reference: Mapped[str | None] = mapped_column(String(256), nullable=True)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source_type: Mapped[str] = mapped_column(String(32), default="SIMULATED")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)


class OcularResult(Base):
    __tablename__ = "ocular_results"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    assessment_id: Mapped[str] = mapped_column(String(36), index=True)
    eye: Mapped[str] = mapped_column(String(16))
    scan_region: Mapped[str] = mapped_column(String(64))
    metric_code: Mapped[str] = mapped_column(String(64))
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(32))
    interpretation: Mapped[str | None] = mapped_column(String(256), nullable=True)


class BoneScan(Base):
    __tablename__ = "bone_scans"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    event_id: Mapped[str] = mapped_column(String(128), unique=True)
    astronaut_id: Mapped[str] = mapped_column(String(128), index=True)
    mission_phase: Mapped[str] = mapped_column(String(32))
    scanned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source_type: Mapped[str] = mapped_column(String(32), default="SIMULATED")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)


class BoneDensityResult(Base):
    __tablename__ = "bone_density_results"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    scan_id: Mapped[str] = mapped_column(String(36), index=True)
    bone_region: Mapped[str] = mapped_column(String(64))
    bmd_value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(32), default="g/cm2")
    t_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    z_score: Mapped[float | None] = mapped_column(Float, nullable=True)


class FitnessAssessment(Base):
    __tablename__ = "fitness_assessments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    event_id: Mapped[str] = mapped_column(String(128), unique=True)
    astronaut_id: Mapped[str] = mapped_column(String(128), index=True)
    test_type: Mapped[str] = mapped_column(String(64))
    metric_code: Mapped[str] = mapped_column(String(64))
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(32))
    protocol: Mapped[str] = mapped_column(String(128))
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source_type: Mapped[str] = mapped_column(String(32), default="SIMULATED")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)


class BiologicalSample(Base):
    __tablename__ = "biological_samples"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    event_id: Mapped[str] = mapped_column(String(128), unique=True)
    astronaut_id: Mapped[str] = mapped_column(String(128), index=True)
    sample_type: Mapped[str] = mapped_column(String(64))
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    processing_status: Mapped[str] = mapped_column(String(32), default="COLLECTED")
    source_type: Mapped[str] = mapped_column(String(32), default="SIMULATED")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)


class ClinicalSampleChain(Base):
    __tablename__ = "clinical_sample_chain"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    sample_id: Mapped[str] = mapped_column(String(36), index=True)
    custody_event: Mapped[str] = mapped_column(String(128))
    responsible_person: Mapped[str] = mapped_column(String(128))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class LaboratoryResult(Base):
    __tablename__ = "laboratory_results"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    event_id: Mapped[str] = mapped_column(String(128), unique=True)
    sample_id: Mapped[str] = mapped_column(String(36), index=True)
    test_code: Mapped[str] = mapped_column(String(64))
    result_value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(32))
    assay_method: Mapped[str] = mapped_column(String(128))
    reviewer_status: Mapped[str] = mapped_column(String(32), default="UNREVIEWED")
    reviewed_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source_type: Mapped[str] = mapped_column(String(32), default="SIMULATED")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)


class SequencingRun(Base):
    __tablename__ = "sequencing_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    event_id: Mapped[str] = mapped_column(String(128), unique=True)
    sample_id: Mapped[str] = mapped_column(String(36), index=True)
    run_id: Mapped[str] = mapped_column(String(128), unique=True)
    platform: Mapped[str] = mapped_column(String(64), default="MINION")
    reads_count: Mapped[int] = mapped_column(Integer)
    yield_bp: Mapped[int] = mapped_column(Integer)
    qc_status: Mapped[str] = mapped_column(String(32))
    source_file_ref: Mapped[str] = mapped_column(String(256))
    reviewer_status: Mapped[str] = mapped_column(String(32), default="PENDING_MANUAL_REVIEW")
    automated_pathogen_diagnosis: Mapped[bool] = mapped_column(Boolean, default=False)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source_type: Mapped[str] = mapped_column(String(32), default="SIMULATED")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)


class NasaResearchStudy(Base):
    __tablename__ = "nasa_research_studies"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(512))
    hazard_category: Mapped[str] = mapped_column(String(128))
    organism_or_domain: Mapped[str] = mapped_column(String(128))
    mission_context: Mapped[str] = mapped_column(String(128))
    source_url: Mapped[str] = mapped_column(String(512))
    summary: Mapped[str] = mapped_column(Text)


class NasaResearchObservation(Base):
    __tablename__ = "nasa_research_observations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    study_id: Mapped[str] = mapped_column(String(64), index=True)
    metric_code: Mapped[str] = mapped_column(String(64))
    group_label: Mapped[str] = mapped_column(String(128))
    mean_value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(32))
    sample_size: Mapped[int] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)