from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


SourceType = Literal["SIMULATED", "SENSOR", "LAB_IMPORT", "MANUAL", "NASA_OSDR_RESEARCH"]
QualityStatus = Literal["VALID", "STALE", "MISSING", "QUARANTINED", "UNVERIFIED"]
VerificationStatus = Literal["UNREVIEWED", "CLINICIAN_REVIEWED", "APPROVED", "DEMO_ONLY", "RESEARCH_ONLY"]


class ProvenanceEnvelope(BaseModel):
    event_id: Optional[str] = None
    source_type: SourceType = "SIMULATED"
    is_synthetic: bool = True
    measured_at: datetime
    received_at: Optional[datetime] = None
    quality_status: QualityStatus = "VALID"
    verification_status: VerificationStatus = "DEMO_ONLY"
    source_device_id: Optional[str] = None


# --- T09: Baselines & Trends ---

class BaselineCreate(BaseModel):
    astronaut_id: str
    metric_code: str
    body_region: str = "WHOLE_BODY"
    measurement_method: str = "STANDARD"
    baseline_value: float
    std_dev: float = 0.0
    unit: str


class TrendComparisonOut(BaseModel):
    astronaut_id: str
    metric_code: str
    body_region: str
    measurement_method: str
    status: Literal["AVAILABLE", "UNAVAILABLE"]
    baseline_value: Optional[float] = None
    latest_value: Optional[float] = None
    delta: Optional[float] = None
    percent_change: Optional[float] = None
    sample_count: int = 0
    unit: Optional[str] = None
    badge: str = "SIMULATED"


# --- T10: Symptoms ---

class SymptomCreate(ProvenanceEnvelope):
    astronaut_id: str
    mission_id: str = "DEMO-01"
    symptom_code: str
    severity: float = Field(ge=0.0, le=10.0)
    onset_at: datetime
    body_location: str = "SYSTEMIC"
    is_sensitive: bool = False
    notes: str = ""


class SymptomOut(SymptomCreate):
    id: str
    incident_triggered: bool = False


# --- T14 & T19: Vitals, ECG & Exercise ---

class VitalCreate(ProvenanceEnvelope):
    astronaut_id: str
    mission_id: str = "DEMO-01"
    metric_code: Literal["HR", "SPO2", "RR", "BP_SYS", "BP_DIA", "TEMP"]
    value: float
    unit: str
    activity_context: Optional[Literal["RESTING", "EXERCISE_ACTIVE", "POST_EXERCISE"]] = None


class VitalOut(BaseModel):
    id: str
    event_id: str
    astronaut_id: str
    metric_code: str
    raw_value: float
    raw_unit: str
    normalized_value: float
    normalized_unit: str
    activity_context: str
    quality_status: str
    verification_status: str
    source_type: str
    is_synthetic: bool
    measured_at: datetime
    received_at: datetime
    alert_generated: Optional[str] = None


class ExerciseSessionCreate(ProvenanceEnvelope):
    astronaut_id: str
    mission_id: str = "DEMO-01"
    exercise_type: str
    started_at: datetime
    ended_at: datetime
    duration_minutes: float = Field(gt=0)
    workload_watts: Optional[float] = None
    repetitions: Optional[int] = None


# --- T15: Radiation & SPE ---

class PersonalDoseCreate(ProvenanceEnvelope):
    astronaut_id: str
    mission_id: str = "DEMO-01"
    dosimeter_id: str
    dose_quantity: Literal["EFFECTIVE_DOSE", "ABSORBED_DOSE", "PARTICLE_FLUX"] = "EFFECTIVE_DOSE"
    particle_type: str = "MIXED_GCR_SPE"
    spectrum_metadata: Dict[str, Any] = Field(default_factory=dict)
    value: float = Field(ge=0)
    unit: str
    interval_hours: float = Field(gt=0, default=1.0)
    location_id: Optional[str] = None


class SpeEventCreate(ProvenanceEnvelope):
    mission_id: str = "DEMO-01"
    event_type: str = "SOLAR_PARTICLE_EVENT"
    started_at: datetime
    ended_at: Optional[datetime] = None
    shelter_location_id: Optional[str] = "HAB-CORE"
    rule_approval_state: Literal["APPROVED", "DEMO_ONLY", "RESEARCH_ONLY"] = "DEMO_ONLY"


# --- T16 & T25: Environment & Microbiology ---

class EnvironmentalReadingCreate(ProvenanceEnvelope):
    location_id: str
    metric_code: Literal["PPCO2", "PPO2", "PRESSURE", "NOISE_DBA", "LIGHT_LUX"]
    value: float
    unit: str
    averaging_window_minutes: int = 60
    weighting_or_spectrum: str = "STANDARD"
    calibration_state: Literal["CALIBRATED", "UNCALIBRATED", "EXPIRED"] = "CALIBRATED"
    rule_approval_state: Literal["APPROVED", "DEMO_ONLY", "RESEARCH_ONLY"] = "DEMO_ONLY"


class EnvironmentalSampleCreate(ProvenanceEnvelope):
    location_id: str
    sample_type: Literal["POTABLE_WATER", "CABIN_AIR", "SURFACE_SWAB", "FOOD"]
    sampling_method: str
    sample_quantity: float = Field(gt=0)
    sample_unit: str
    collected_at: Optional[datetime] = None
    test_code: str
    result_value: float = Field(ge=0)
    result_unit: str
    standard_revision: str = "DEMO_CRITERIA_V1"
    rule_approval_state: Literal["APPROVED", "DEMO_ONLY", "RESEARCH_ONLY"] = "DEMO_ONLY"


# --- T17: Gravity Transition ---

class GravityAssessmentCreate(ProvenanceEnvelope):
    astronaut_id: str
    gravity_event_id: Optional[str] = None
    symptom_score: float = Field(ge=0, le=10)
    reaction_time_ms: float = Field(gt=0)
    assessed_at: datetime


# --- T18: Sleep, Nutrition & Behavioral Check-ins ---

class SleepSessionCreate(ProvenanceEnvelope):
    astronaut_id: str
    start_at: datetime
    end_at: datetime
    duration_hours: float = Field(ge=0)
    awakenings_count: int = Field(ge=0, default=0)


class BehavioralCheckinCreate(ProvenanceEnvelope):
    astronaut_id: str
    assessment_type: str = "DAILY_PSYCH_CHECKIN"
    mood_score: float = Field(ge=1, le=10)
    fatigue_score: float = Field(ge=1, le=10)
    stress_score: float = Field(ge=1, le=10)
    visibility_classification: Literal["PRIVATE_CLINICAL", "CREW_RESTRICTED", "MISSION_COMMAND"] = "PRIVATE_CLINICAL"
    confidential_notes: str = ""


# --- T20–T24: Examinations, Vascular, Ocular, Bone & Samples ---

class VascularUltrasoundCreate(ProvenanceEnvelope):
    astronaut_id: str
    vein: str = "INTERNAL_JUGULAR"
    side: Literal["LEFT", "RIGHT"]
    flow_pattern: Literal["NORMAL_PHASIC", "STAGNANT", "REVERSED"]
    thrombus_finding: Literal["NONE_OBSERVED", "SUSPECTED_REVIEW_REQUIRED", "CONFIRMED_BY_CLINICIAN"]
    reviewed_by: Optional[str] = None


class OcularMeasurementInput(BaseModel):
    eye: Literal["LEFT", "RIGHT"]
    scan_region: str = "RNFL_GLOBAL"
    metric_code: str
    value: float
    unit: str
    interpretation: str = "UNREVIEWED"


class OcularAssessmentCreate(ProvenanceEnvelope):
    astronaut_id: str
    test_type: Literal["OCT", "VISUAL_ACUITY", "FUNDOSCOPY"]
    assessed_at: datetime
    report_reference: str = ""
    results: List[OcularMeasurementInput]


class BoneScanCreate(ProvenanceEnvelope):
    astronaut_id: str
    mission_phase: Literal["PREFLIGHT", "INFLIGHT", "POSTFLIGHT", "RECOVERY"]
    scanned_at: datetime
    bone_region: Literal["LUMBAR_SPINE", "TOTAL_HIP", "FEMORAL_NECK"]
    bmd_value: float
    unit: str = "g/cm2"
    t_score: float
    z_score: float


class LabResultCreate(ProvenanceEnvelope):
    astronaut_id: str
    sample_type: Literal["BLOOD", "SALIVA", "URINE", "SWAB"]
    custody_actor: str
    test_code: str
    result_value: float
    unit: str
    assay_method: str
    reference_low: Optional[float] = None
    reference_high: Optional[float] = None
    clinician_review_status: Literal["UNREVIEWED", "CLINICIAN_REVIEWED"] = "UNREVIEWED"


class SequencingRunCreate(ProvenanceEnvelope):
    sample_id: str
    platform: str = "OXFORD_NANOPORE_MINION"
    reads_count: int = Field(ge=0)
    yield_mb: float = Field(ge=0)
    mean_q_score: float = Field(ge=0)
    data_reference: str


# --- T29: Simulation Control ---

class ScenarioRunRequest(BaseModel):
    scenario_id: Literal["S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08", "S09", "S10", "S11", "S12"]
    seed: int = 20261115
    at_timestamp: Optional[datetime] = None