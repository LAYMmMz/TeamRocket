from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.dev1_bridge import Dev1IntegrationBridge
from app.models.dev2_models import PersonalDoseRecord, RadiationEvent, new_uuid
from app.schemas.dev2_schemas import PersonalDoseCreate, SpeEventCreate


EFFECTIVE_DOSE_UNITS = {"mSv": 1.0, "uSv": 0.001, "Sv": 1000.0}
ABSORBED_DOSE_UNITS = {"mGy": 1.0, "cGy": 10.0, "Gy": 1000.0}
PARTICLE_SPECTRUM_UNITS = {"particles/cm2/s", "protons/cm2/s/sr", "MeV/nuc"}


class RadiationService:
    @staticmethod
    def ingest_personal_dose(db: Session, payload: PersonalDoseCreate) -> Dict[str, Any]:
        # Task 15: Enforce strict unit & quantity compatibility; never convert particle spectra to Sv without coefficients
        if payload.dose_quantity == "EFFECTIVE_DOSE":
            if payload.unit not in EFFECTIVE_DOSE_UNITS:
                raise HTTPException(
                    status_code=422,
                    detail=f"Incompatible effective dose unit '{payload.unit}'. Particle values cannot be summed into mSv without approved quality-factor coefficients.",
                )
            norm_val = round(payload.value * EFFECTIVE_DOSE_UNITS[payload.unit], 5)
            norm_unit = "mSv"
        elif payload.dose_quantity == "ABSORBED_DOSE":
            if payload.unit not in ABSORBED_DOSE_UNITS:
                raise HTTPException(
                    status_code=422,
                    detail=f"Incompatible absorbed dose unit '{payload.unit}'.",
                )
            norm_val = round(payload.value * ABSORBED_DOSE_UNITS[payload.unit], 5)
            norm_unit = "mGy"
        else:
            if payload.unit not in PARTICLE_SPECTRUM_UNITS:
                raise HTTPException(
                    status_code=422,
                    detail=f"Unsupported particle spectrum unit '{payload.unit}'.",
                )
            norm_val = payload.value
            norm_unit = payload.unit

        rec = PersonalDoseRecord(
            event_id=payload.event_id or new_uuid(),
            astronaut_id=payload.astronaut_id,
            mission_id=payload.mission_id,
            dosimeter_id=payload.dosimeter_id,
            dose_quantity=payload.dose_quantity,
            particle_type=payload.particle_type,
            spectrum_metadata=payload.spectrum_metadata,
            raw_value=payload.value,
            raw_unit=payload.unit,
            normalized_value=norm_val,
            normalized_unit=norm_unit,
            interval_hours=payload.interval_hours,
            location_id=payload.location_id,
            measured_at=payload.measured_at,
            source_type=payload.source_type,
            is_synthetic=payload.is_synthetic,
            quality_status=payload.quality_status,
            verification_status=payload.verification_status,
        )
        db.add(rec)
        db.flush()
        return {
            "id": rec.id,
            "dose_quantity": rec.dose_quantity,
            "normalized_value": rec.normalized_value,
            "normalized_unit": rec.normalized_unit,
            "quality_status": rec.quality_status,
            "verification_status": rec.verification_status,
        }

    @staticmethod
    def trigger_spe_event(
        db: Session,
        payload: SpeEventCreate,
        astronaut_ids: List[str],
    ) -> Dict[str, Any]:
        settings = get_settings()
        spe = RadiationEvent(
            event_id=payload.event_id or new_uuid(),
            mission_id=payload.mission_id,
            event_type=payload.event_type,
            started_at=payload.started_at,
            ended_at=payload.ended_at,
            status="ACTIVE",
            shelter_location_id=payload.shelter_location_id,
            rule_approval_state=payload.rule_approval_state,
            measured_at=payload.measured_at,
            source_type=payload.source_type,
            is_synthetic=payload.is_synthetic,
            verification_status=payload.rule_approval_state,
        )
        db.add(spe)
        db.flush()

        now = datetime.now(timezone.utc)
        stale_crew: List[str] = []
        for astro_id in astronaut_ids:
            latest_dose = db.scalars(
                select(PersonalDoseRecord)
                .where(PersonalDoseRecord.astronaut_id == astro_id)
                .order_by(PersonalDoseRecord.measured_at.desc())
            ).first()
            is_stale = True
            if latest_dose:
                m_time = latest_dose.measured_at if latest_dose.measured_at.tzinfo else latest_dose.measured_at.replace(tzinfo=timezone.utc)
                is_stale = (now - m_time) > timedelta(hours=settings.dosimeter_stale_after_hours) or latest_dose.quality_status == "STALE"
            if is_stale:
                stale_crew.append(astro_id)

        alert_res = Dev1IntegrationBridge.emit_alert_and_optional_incident(
            db=db,
            rule_id="RULE-SPE-SHELTER-ADVISORY",
            rule_version="1.0.0",
            rule_approval_status=payload.rule_approval_state,
            severity="WARNING",
            title=f"Solar Particle Event active ({payload.rule_approval_state}) — review shelter guidance for {payload.shelter_location_id}",
            evidence_refs=[f"radiation_events:{spe.id}"],
            location_id=payload.shelter_location_id,
            open_incident=True,
            incident_type="SOLAR_PARTICLE_EVENT",
            is_synthetic=payload.is_synthetic,
        )

        return {
            "spe_event_id": spe.id,
            "rule_approval_state": payload.rule_approval_state,
            "stale_dosimeter_crew": stale_crew,
            "reference_limits_note": {
                "career_msv": settings.radiation_career_ref_msv,
                "spe_msv": settings.radiation_spe_ref_msv,
                "classification": "RESEARCH_REFERENCE_ONLY_UNLESS_APPROVED",
            },
            "alert_id": alert_res["alert_id"],
            "incident_id": alert_res["incident_id"],
        }

    @staticmethod
    def get_astronaut_cumulative_dose(db: Session, astronaut_id: str) -> Dict[str, Any]:
        settings = get_settings()
        records = db.scalars(
            select(PersonalDoseRecord).where(
                PersonalDoseRecord.astronaut_id == astronaut_id,
                PersonalDoseRecord.dose_quantity == "EFFECTIVE_DOSE",
                PersonalDoseRecord.normalized_unit == "mSv",
            )
        ).all()
        total_msv = round(sum(r.normalized_value for r in records), 4)
        stale_count = sum(1 for r in records if r.quality_status == "STALE")
        return {
            "astronaut_id": astronaut_id,
            "cumulative_effective_dose_msv": total_msv,
            "compatible_record_count": len(records),
            "stale_record_count": stale_count,
            "research_reference_career_msv": settings.radiation_career_ref_msv,
            "research_reference_spe_msv": settings.radiation_spe_ref_msv,
            "reference_gating": "RESEARCH_ONLY",
        }