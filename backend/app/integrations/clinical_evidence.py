"""Mission-authorized read views for synthetic Dev2 examination and laboratory evidence.

This is the *local SQLite research fixture* adapter, NOT a cloud verification
endpoint and never part of the anonymous judges' public API. No cross-crew
joins or unapproved synthetic indices are substituted for clinical evidence.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.auth.dependencies import require
from app.core.dependencies import get_settings
from app.core.db import SessionLocal
from app.models.dev2_models import (
    BiologicalSample, BoneDensityResult, BoneScan, ClinicalSampleChain,
    FitnessAssessment, LaboratoryResult,
    OcularAssessment, OcularResult, SequencingRun, VascularUltrasoundResult,
)

router = APIRouter(prefix="/api/v1/clinical", tags=["Authorized synthetic clinical evidence"])
DEMO_MISSION = "DEMO-01"
CLINICAL_ROLES = frozenset({"admin", "flight_surgeon"})


def _authorize(principal, mission_id, settings):
    principal.require_mission(mission_id)
    if not CLINICAL_ROLES.intersection(principal.roles):
        principal.deny("clinical:evidence_read", mission_id=mission_id)
    # Local Dev2 fixtures have no production Supabase mission linkage:
    # never surface them as production clinical data or another mission.
    return mission_id == DEMO_MISSION and settings.environment in {"development", "test"}


def _row(kind, record_id, label, value, unit, measured_at, details, *,
         review="UNREVIEWED", source="SIMULATED"):
    return {
        "id": str(record_id), "label": str(label), "value": str(value),
        "unit": str(unit or ""), "measured_at": measured_at.isoformat(),
        "source": source, "quality": str(review),
        "details": str(details), "record_table": kind, "is_synthetic": True,
    }


@router.get("/examinations/{astronaut_id}")
def examination_evidence(
    astronaut_id: str, mission_id: str = DEMO_MISSION,
    principal=Depends(require("measurements:read")),
    settings=Depends(get_settings),
):
    if not _authorize(principal, mission_id, settings):
        return []
    items = []
    with SessionLocal() as db:
        vascular = db.scalars(select(VascularUltrasoundResult).where(
            VascularUltrasoundResult.astronaut_id == astronaut_id,
            VascularUltrasoundResult.is_synthetic.is_(True),
        ).order_by(VascularUltrasoundResult.measured_at.desc()).limit(40)).all()
        for r in vascular:
            items.append(_row("vascular_ultrasound_results", r.id,
                f"{r.side} {r.vein} Doppler", r.flow_pattern, "",
                r.measured_at,
                f"Side={r.side}; thrombus finding={r.thrombus_finding}; reviewed_by={r.reviewed_by or 'unassigned'}; event_id={r.event_id}",
                review=r.verification_status, source=r.source_type))

        eyes = db.execute(select(OcularResult, OcularAssessment)
            .join(OcularAssessment, OcularResult.assessment_id == OcularAssessment.id)
            .where(OcularAssessment.astronaut_id == astronaut_id,
                   OcularAssessment.is_synthetic.is_(True))
            .order_by(OcularAssessment.assessed_at.desc()).limit(40)).all()
        for r, parent in eyes:
            items.append(_row("ocular_results", r.id,
                f"{r.eye} {r.scan_region} {r.metric_code}", r.value, r.unit,
                parent.assessed_at,
                f"Test={parent.test_type}; eye={r.eye}; region={r.scan_region}; assessment_id={parent.id}; event_id={parent.event_id}",
                review="REVIEW_REQUIRED", source=parent.source_type))

        density = db.execute(select(BoneDensityResult, BoneScan)
            .join(BoneScan, BoneDensityResult.scan_id == BoneScan.id)
            .where(BoneScan.astronaut_id == astronaut_id,
                   BoneScan.is_synthetic.is_(True),
                   BoneScan.mission_phase.in_(["PREFLIGHT", "POSTFLIGHT", "RECOVERY"]))
            .order_by(BoneScan.scanned_at.desc()).limit(40)).all()
        for r, parent in density:
            items.append(_row("bone_density_results", r.id,
                f"{parent.mission_phase} DXA — {r.bone_region}", r.bmd_value, r.unit,
                parent.scanned_at,
                f"Region={r.bone_region}; phase={parent.mission_phase}; scan_id={parent.id}; event_id={parent.event_id}; no in-flight DXA inferred",
                review="REVIEW_REQUIRED", source=parent.source_type))

        fitness = db.scalars(select(FitnessAssessment).where(
            FitnessAssessment.astronaut_id == astronaut_id,
            FitnessAssessment.is_synthetic.is_(True),
        ).order_by(FitnessAssessment.assessed_at.desc()).limit(40)).all()
        for r in fitness:
            items.append(_row("fitness_assessments", r.id,
                f"{r.test_type} {r.metric_code}", r.value, r.unit,
                r.assessed_at,
                f"Protocol={r.protocol}; event_id={r.event_id}",
                source=r.source_type))

    return sorted(items, key=lambda r: r["measured_at"], reverse=True)[:120]


@router.get("/laboratory/{astronaut_id}")
def laboratory_evidence(
    astronaut_id: str, mission_id: str = DEMO_MISSION,
    principal=Depends(require("measurements:read")),
    settings=Depends(get_settings),
):
    if not _authorize(principal, mission_id, settings):
        return []
    items = []
    with SessionLocal() as db:
        sample_ids = db.scalars(select(BiologicalSample.id).where(
            BiologicalSample.astronaut_id == astronaut_id,
            BiologicalSample.is_synthetic.is_(True),
        ).limit(120)).all()
        if not sample_ids:
            return []
        samples = db.scalars(select(BiologicalSample).where(
            BiologicalSample.id.in_(sample_ids))
            .order_by(BiologicalSample.collected_at.desc())).all()
        for s in samples:
            items.append(_row("biological_samples", s.id,
                f"Sample: {s.sample_type}", s.processing_status, "",
                s.collected_at, f"Sample ID={s.id}; event_id={s.event_id}",
                review="PROCESSING_STATUS", source=s.source_type))

        results = db.scalars(select(LaboratoryResult).where(
            LaboratoryResult.sample_id.in_(sample_ids),
            LaboratoryResult.is_synthetic.is_(True),
        ).order_by(LaboratoryResult.measured_at.desc()).limit(120)).all()
        for r in results:
            items.append(_row("laboratory_results", r.id,
                r.test_code, r.result_value, r.unit, r.measured_at,
                f"Sample ID={r.sample_id}; assay={r.assay_method}; reviewer={r.reviewed_by or 'unassigned'}; event_id={r.event_id}; never an automatic diagnosis",
                review=r.reviewer_status, source=r.source_type))

        runs = db.scalars(select(SequencingRun).where(
            SequencingRun.sample_id.in_(sample_ids),
            SequencingRun.is_synthetic.is_(True),
        ).order_by(SequencingRun.measured_at.desc()).limit(40)).all()
        for r in runs:
            items.append(_row("sequencing_runs", r.id,
                f"{r.platform} {r.run_id}", r.reads_count, "reads",
                r.measured_at,
                f"Sample ID={r.sample_id}; yield_bp={r.yield_bp}; QC={r.qc_status}; review={r.reviewer_status}; no pathogen diagnosis",
                review=r.reviewer_status, source=r.source_type))

        custody = db.scalars(select(ClinicalSampleChain).where(
            ClinicalSampleChain.sample_id.in_(sample_ids))
            .order_by(ClinicalSampleChain.occurred_at.desc()).limit(120)).all()
        for r in custody:
            items.append(_row("clinical_sample_chain", r.id,
                "Custody: " + r.custody_event, "Recorded", "",
                r.occurred_at,
                f"Sample ID={r.sample_id}; responsible actor={r.responsible_person}",
                review="CUSTODY_EVENT"))
    return sorted(items, key=lambda r: r["measured_at"], reverse=True)[:160]
