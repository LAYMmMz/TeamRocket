"""Typed, provenance-preserving domain evidence contracts.

This is a prototype staging API, not a clinical diagnostic or prescribing service.
Domain records are stored in encrypted Dev 1 SQLite only; they are NOT automatically
written into the unreviewed Supabase schema or the plaintext teammate database.
"""
from __future__ import annotations
import math
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, AwareDatetime, model_validator

# Task owners: T09, T14-T25; this identifies API boundaries, not a claim that all
# clinical analysis/approval behavior required by those tasks is implemented.
DOMAIN_FIELDS = {
    "baselines": ("metric_code", "baseline_value", "measurement_method", "validity"),
    "radiation": ("dose_quantity", "original_value", "original_unit", "interval_start", "interval_end", "particle_type"),
    "environment": ("metric_code", "original_value", "original_unit", "zone", "averaging_window_seconds", "calibration_revision"),
    "gravity": ("transition_type", "gravity_level", "assessment_status"),
    "sleep": ("start_at", "end_at"),
    "nutrition": ("intake_details", "original_value", "original_unit"),
    "behavioral": ("assessment_type", "visibility_classification"),
    "hydration": ("assessment_type", "review_status"),
    "ecg": ("report_reference", "review_status"),
    "habitat_events": ("event_type", "zone", "review_status"),
    "dose_events": ("event_type", "location", "review_status"),
    "environmental_results": ("sample_id", "method", "review_status"),
    "exercise": ("exercise_type", "duration_minutes", "activity_context"),
    "exams": ("exam_type", "scheduled_at", "status", "template_source"),
    "samples": ("sample_id", "sample_type", "collected_at", "processing_status"),
    "lab_results": ("sample_id", "assay_code", "result_status", "method", "review_status"),
    "sequencing": ("sample_id", "run_id", "platform", "reads", "yield_bases", "qc_status", "review_status"),
    "vascular": ("exam_id", "side", "method", "review_status"),
    "ocular": ("exam_id", "eye", "region", "method", "review_status"),
    "bone": ("exam_id", "anatomical_region", "method", "flight_phase", "review_status"),
    "fitness": ("assessment_type", "test_method", "flight_phase", "review_status"),
    "environmental_samples": ("sample_id", "sample_type", "sampling_method", "denominator_unit", "review_status"),
    "symptoms": ("symptom_code", "onset_at", "body_location", "severity_category", "review_status"),
}
PRIVATE_DOMAINS = frozenset({"behavioral"})

class DomainEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    event_id: str = Field(min_length=1, max_length=128)
    mission_id: str = Field(min_length=1, max_length=128)
    astronaut_id: str | None = Field(default=None, max_length=128)
    source_type: Literal["SIMULATED", "REAL", "RESEARCH"]
    is_synthetic: bool
    measured_at: AwareDatetime
    received_at: AwareDatetime
    quality: Literal["VALID", "SUSPECT", "INVALID", "MISSING", "STALE"]
    verification: Literal["VERIFIED", "UNVERIFIED", "REJECTED"]
    source_reference: str = Field(min_length=1, max_length=2048)
    source_revision: str = Field(min_length=1, max_length=128)
    data: dict[str, Any]

    @model_validator(mode="after")
    def consistency(self):
        if self.is_synthetic != (self.source_type == "SIMULATED"):
            raise ValueError("is_synthetic must agree with source_type")
        if self.measured_at > self.received_at:
            raise ValueError("measured_at cannot be after received_at")
        if not self.data:
            raise ValueError("data must not be empty")
        return self


def validate_domain(domain: str, event: DomainEvent) -> dict:
    """Return validated storage payload. Missing source cannot become normal."""
    if domain not in DOMAIN_FIELDS:
        raise ValueError("Unknown domain")
    required = DOMAIN_FIELDS[domain]
    missing = [field for field in required if field not in event.data or event.data[field] is None]
    if missing:
        raise ValueError("Missing required fields: " + ", ".join(missing))
    d = event.data
    if domain == "radiation":
        start = datetime.fromisoformat(str(d["interval_start"]).replace("Z", "+00:00"))
        end = datetime.fromisoformat(str(d["interval_end"]).replace("Z", "+00:00"))
        if start.tzinfo is None or end.tzinfo is None or start >= end:
            raise ValueError("Radiation interval must have ordered timezone-aware timestamps")
        if d["dose_quantity"] not in {"effective", "equivalent", "absorbed", "rate"}:
            raise ValueError("Unsupported radiation quantity")
        if d["dose_quantity"] in {"effective", "equivalent"} and d["original_unit"] not in {"Sv", "mSv", "uSv"}:
            raise ValueError("Effective/equivalent dose must use a compatible dose unit")
        if d["dose_quantity"] == "absorbed" and d["original_unit"] not in {"Gy", "mGy"}:
            raise ValueError("Absorbed dose requires Gy or mGy")
        if d["dose_quantity"] == "rate" and d["original_unit"] not in {"uSv/h", "mSv/h"}:
            raise ValueError("Dose rate must not be added to cumulative dose")
    if domain == "environment":
        if not isinstance(d["averaging_window_seconds"], (int, float)) or isinstance(d["averaging_window_seconds"], bool) or d["averaging_window_seconds"] <= 0:
            raise ValueError("Positive averaging_window_seconds is required")
        if d["metric_code"] == "noise" and d.get("weighting") != "A":
            raise ValueError("dB(A) noise requires weighting A")
    if domain == "vascular" and d["side"] not in {"LEFT", "RIGHT"}:
        raise ValueError("Side must be LEFT or RIGHT")
    if domain == "ocular" and d["eye"] not in {"LEFT", "RIGHT"}:
        raise ValueError("Eye must be LEFT or RIGHT")
    if domain == "bone" and d["flight_phase"] not in {"PRE", "POST"}:
        raise ValueError("Demo bone comparison must not fabricate in-flight DXA results")
    if domain == "symptoms" and d["severity_category"] not in {"minor", "moderate", "serious", "severe", "critical"}:
        raise ValueError("Categorical symptom scale must not be inferred as numeric severity")
    if domain in {"radiation", "environment", "nutrition"}:
        value = d.get("original_value")
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
            raise ValueError("Finite numeric original_value required")
    if domain == "exercise" and (not isinstance(d.get("duration_minutes"), (int, float)) or isinstance(d.get("duration_minutes"), bool) or d["duration_minutes"] <= 0):
        raise ValueError("Exercise duration must be positive")
    if domain == "exams" and d["status"] not in {"PLANNED", "DUE", "OVERDUE", "COMPLETED", "CANCELLED"}:
        raise ValueError("Unsupported medical examination status")
    if domain == "behavioral" and d["visibility_classification"] not in {"PRIVATE", "CLINICIAN_REVIEW"}:
        raise ValueError("Behavioral results must be private")
    return event.model_dump(mode="json") | {"domain": domain}
