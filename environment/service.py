from __future__ import annotations

from datetime import timedelta, timezone
from typing import Any, Dict, Tuple
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.dev1_bridge import Dev1IntegrationBridge
from app.models.dev2_models import EnvironmentalLabResult, EnvironmentalReading, EnvironmentalSample, new_uuid
from app.schemas.dev2_schemas import EnvironmentalReadingCreate, EnvironmentalSampleCreate


ENV_UNIT_CONVERSIONS: Dict[str, Dict[str, Tuple[str, float]]] = {
    "PPCO2": {"mmHg": ("mmHg", 1.0), "kPa": ("mmHg", 7.50062)},
    "PPO2": {"mmHg": ("mmHg", 1.0), "kPa": ("mmHg", 7.50062)},
    "PRESSURE": {"kPa": ("kPa", 1.0), "mmHg": ("kPa", 0.133322)},
    "NOISE_DBA": {"dB(A)": ("dB(A)", 1.0)},
    "LIGHT_LUX": {"lux": ("lux", 1.0)},
}

REQUIRED_CFU_DENOMINATORS: Dict[str, Tuple[str, float, str]] = {
    "POTABLE_WATER": ("CFU/100mL", 50.0, "POTABLE_WATER_RESTRICTION_AND_RESAMPLE"),
    "CABIN_AIR": ("CFU/m3", 1000.0, "VENTILATION_HEPA_REVIEW_AND_RESAMPLE"),
    "SURFACE_SWAB": ("CFU/cm2", 100.0, "SURFACE_DISINFECTION_AND_RESAMPLE"),
    "FOOD": ("CFU/g", 10000.0, "FOOD_LOT_QUARANTINE_AND_RESAMPLE"),
}


class EnvironmentService:
    @staticmethod
    def ingest_reading(db: Session, payload: EnvironmentalReadingCreate) -> Dict[str, Any]:
        settings = get_settings()
        allowed = ENV_UNIT_CONVERSIONS.get(payload.metric_code, {})
        if payload.unit not in allowed:
            raise HTTPException(
                status_code=422,
                detail=f"Incompatible unit '{payload.unit}' for environmental metric '{payload.metric_code}'.",
            )
        norm_unit, factor = allowed[payload.unit]
        norm_val = round(payload.value * factor, 4)

        reading = EnvironmentalReading(
            event_id=payload.event_id or new_uuid(),
            location_id=payload.location_id,
            metric_code=payload.metric_code,
            raw_value=payload.value,
            raw_unit=payload.unit,
            normalized_value=norm_val,
            normalized_unit=norm_unit,
            averaging_window_minutes=payload.averaging_window_minutes,
            weighting_or_spectrum=payload.weighting_or_spectrum,
            calibration_state=payload.calibration_state,
            rule_approval_state=payload.rule_approval_state,
            measured_at=payload.measured_at,
            source_type=payload.source_type,
            is_synthetic=payload.is_synthetic,
            quality_status="UNVERIFIED" if payload.calibration_state != "CALIBRATED" else payload.quality_status,
            verification_status=payload.rule_approval_state,
        )
        db.add(reading)
        db.flush()

        rolling_avg = norm_val
        alert_info = None

        # Task 16 & S04: Evaluate ppCO2 over a 1-hour rolling window rather than instantaneous spike alone
        if payload.metric_code == "PPCO2" and payload.calibration_state == "CALIBRATED":
            m_utc = payload.measured_at if payload.measured_at.tzinfo else payload.measured_at.replace(tzinfo=timezone.utc)
            window_start = m_utc - timedelta(minutes=settings.co2_averaging_window_minutes)
            window_rows = db.scalars(
                select(EnvironmentalReading).where(
                    EnvironmentalReading.location_id == payload.location_id,
                    EnvironmentalReading.metric_code == "PPCO2",
                    EnvironmentalReading.measured_at >= window_start,
                    EnvironmentalReading.measured_at <= m_utc,
                )
            ).all()
            if window_rows:
                rolling_avg = round(sum(r.normalized_value for r in window_rows) / len(window_rows), 4)

            if rolling_avg > settings.co2_demo_threshold_mmhg:
                if payload.rule_approval_state in {"APPROVED", "DEMO_ONLY"}:
                    severity = "WARNING" if payload.rule_approval_state == "APPROVED" else "ADVISORY"
                    label = "APPROVED" if payload.rule_approval_state == "APPROVED" else "DEMO-ONLY"
                    alert_info = Dev1IntegrationBridge.emit_alert_and_optional_incident(
                        db=db,
                        rule_id="RULE-ENV-CO2-1HR-WINDOW",
                        rule_version="1.0.0",
                        rule_approval_status=payload.rule_approval_state,
                        severity=severity,
                        title=f"[{label}] 1-hr rolling ppCO2 elevated in {payload.location_id} ({rolling_avg} mmHg)",
                        evidence_refs=[f"environmental_readings:{reading.id}"],
                        location_id=payload.location_id,
                        open_incident=True,
                        incident_type="CO2_AND_HEADACHE_CORRELATED_REVIEW",
                        is_synthetic=payload.is_synthetic,
                    )

        return {
            "id": reading.id,
            "location_id": reading.location_id,
            "metric_code": reading.metric_code,
            "normalized_value": norm_val,
            "normalized_unit": norm_unit,
            "rolling_1h_average": rolling_avg if payload.metric_code == "PPCO2" else None,
            "rule_approval_state": payload.rule_approval_state,
            "alert": alert_info,
        }

    @staticmethod
    def ingest_microbiology_sample(db: Session, payload: EnvironmentalSampleCreate) -> Dict[str, Any]:
        # Task 25 & S09: Enforce strict per-method CFU denominator matching
        expected_unit, demo_limit, remediation_cmd = REQUIRED_CFU_DENOMINATORS[payload.sample_type]
        if payload.result_unit != expected_unit:
            raise HTTPException(
                status_code=422,
                detail=f"{payload.sample_type} requires '{expected_unit}' denominator, received '{payload.result_unit}'.",
            )

        sample = EnvironmentalSample(
            event_id=payload.event_id or new_uuid(),
            location_id=payload.location_id,
            sample_type=payload.sample_type,
            sampling_method=payload.sampling_method,
            sample_quantity=payload.sample_quantity,
            sample_unit=payload.sample_unit,
            collected_at=payload.collected_at or payload.measured_at,
            measured_at=payload.measured_at,
            source_type=payload.source_type,
            is_synthetic=payload.is_synthetic,
        )
        db.add(sample)
        db.flush()

        exceeded = payload.result_value > demo_limit
        result = EnvironmentalLabResult(
            event_id=new_uuid(),
            sample_id=sample.id,
            test_code=payload.test_code,
            result_value=payload.result_value,
            unit=payload.result_unit,
            standard_revision=payload.standard_revision,
            rule_approval_state=payload.rule_approval_state,
            remediation_required=exceeded,
            remediation_action=remediation_cmd if exceeded else None,
            measured_at=payload.measured_at,
            source_type=payload.source_type,
            is_synthetic=payload.is_synthetic,
            verification_status=payload.rule_approval_state,
        )
        db.add(result)
        db.flush()

        alert_info = None
        if exceeded:
            alert_info = Dev1IntegrationBridge.emit_alert_and_optional_incident(
                db=db,
                rule_id=f"RULE-MICRO-{payload.sample_type}",
                rule_version=payload.standard_revision,
                rule_approval_status=payload.rule_approval_state,
                severity="WARNING",
                title=f"[{payload.rule_approval_state}] {payload.sample_type} microbial exceedance ({payload.result_value} {payload.result_unit}) — {remediation_cmd}",
                evidence_refs=[f"environmental_lab_results:{result.id}"],
                location_id=payload.location_id,
                open_incident=False,
                is_synthetic=payload.is_synthetic,
            )

        return {
            "sample_id": sample.id,
            "result_id": result.id,
            "sample_type": payload.sample_type,
            "result_value": payload.result_value,
            "unit": payload.result_unit,
            "remediation_required": exceeded,
            "remediation_action": remediation_cmd if exceeded else None,
            "repeat_sampling_scheduled": exceeded,
            "rule_approval_state": payload.rule_approval_state,
            "alert": alert_info,
        }