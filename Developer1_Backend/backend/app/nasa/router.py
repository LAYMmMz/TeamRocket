from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dev1_bridge import ActorContext, get_actor_context
from app.models.dev2_models import NasaResearchObservation, NasaResearchStudy

router = APIRouter(prefix="/api/nasa", tags=["nasa research & osdr evidence"])

DEFAULT_OSDR_STUDIES = [
    {
        "id": "OSD-104",
        "title": "ISS Microbial Tracking-2: Metagenomic & Cultural Surveillance of Spaceflight Surfaces and Air",
        "hazard_category": "HOSTILE_CLOSED_ENVIRONMENTS",
        "organism_or_domain": "Microbiome / Environmental",
        "mission_context": "ISS Long-Duration",
        "source_url": "https://osdr.nasa.gov/bio/repo/data/studies/OSD-104",
        "summary": "Reference spaceflight microbial burden observations (historical context only; never used as personal clinical diagnostic cutoffs).",
        "observations": [
            {
                "metric_code": "CABIN_SURFACE_BACTERIA",
                "group_label": "ISS Node 2 Reference",
                "mean_value": 420.0,
                "unit": "CFU/100cm2",
                "sample_size": 24,
                "notes": "Historical OSDR reference observation; NASA-STD-3001 in-flight ceiling is 10,000 CFU/100cm2.",
            }
        ],
    },
    {
        "id": "OSD-249",
        "title": "Spaceflight Standard Measures: Sleep Actigraphy & Circadian Alignment in Microgravity",
        "hazard_category": "ISOLATION_AND_CONFINEMENT",
        "organism_or_domain": "Human Physiology",
        "mission_context": "ISS 6-Month Expeditions",
        "source_url": "https://osdr.nasa.gov/bio/repo/data/studies/OSD-249",
        "summary": "Historical actigraphy distribution showing 6.0-6.5 hr average on-orbit sleep (context only, not a clinical target).",
        "observations": [
            {
                "metric_code": "SLEEP_DURATION_MINUTES",
                "group_label": "On-Orbit Actigraphy Cohort",
                "mean_value": 378.0,
                "unit": "minutes",
                "sample_size": 36,
                "notes": "6.3 hours historical mean; optimal clinical recovery target remains 7-9 hours.",
            }
        ],
    },
]


def _ensure_reference_studies(db: Session) -> None:
    if db.scalars(select(NasaResearchStudy)).first() is not None:
        return
    for item in DEFAULT_OSDR_STUDIES:
        db.add(
            NasaResearchStudy(
                id=item["id"],
                title=item["title"],
                hazard_category=item["hazard_category"],
                organism_or_domain=item["organism_or_domain"],
                mission_context=item["mission_context"],
                source_url=item["source_url"],
                summary=item["summary"],
            )
        )
        for obs in item["observations"]:
            db.add(
                NasaResearchObservation(
                    study_id=item["id"],
                    metric_code=obs["metric_code"],
                    group_label=obs["group_label"],
                    mean_value=obs["mean_value"],
                    unit=obs["unit"],
                    sample_size=obs["sample_size"],
                    notes=obs["notes"],
                )
            )
    db.flush()


@router.get("/studies")
def list_nasa_studies(
    db: Session = Depends(get_db),
    _actor: ActorContext = Depends(get_actor_context),
):
    _ensure_reference_studies(db)
    studies = db.scalars(select(NasaResearchStudy)).all()
    return {
        "classification": "NASA_OSDR_REFERENCE_DATA",
        "is_clinical_threshold": False,
        "items": [
            {
                "id": s.id,
                "title": s.title,
                "hazard_category": s.hazard_category,
                "organism_or_domain": s.organism_or_domain,
                "mission_context": s.mission_context,
                "source_url": s.source_url,
                "summary": s.summary,
            }
            for s in studies
        ],
    }


@router.get("/studies/{study_id}")
def get_nasa_study(
    study_id: str,
    db: Session = Depends(get_db),
    _actor: ActorContext = Depends(get_actor_context),
):
    _ensure_reference_studies(db)
    study = db.get(NasaResearchStudy, study_id)
    if study is None:
        raise HTTPException(status_code=404, detail=f"NASA study '{study_id}' not found.")
    return {
        "id": study.id,
        "title": study.title,
        "hazard_category": study.hazard_category,
        "organism_or_domain": study.organism_or_domain,
        "mission_context": study.mission_context,
        "source_url": study.source_url,
        "summary": study.summary,
        "classification": "NASA_OSDR_REFERENCE_DATA",
    }


@router.get("/studies/{study_id}/observations")
def get_nasa_study_observations(
    study_id: str,
    db: Session = Depends(get_db),
    _actor: ActorContext = Depends(get_actor_context),
):
    _ensure_reference_studies(db)
    study = db.get(NasaResearchStudy, study_id)
    if study is None:
        raise HTTPException(status_code=404, detail=f"NASA study '{study_id}' not found.")
    rows = db.scalars(
        select(NasaResearchObservation).where(NasaResearchObservation.study_id == study_id)
    ).all()
    return {
        "study_id": study_id,
        "classification": "NASA_OSDR_REFERENCE_DATA",
        "is_clinical_threshold": False,
        "observations": [
            {
                "id": r.id,
                "metric_code": r.metric_code,
                "group_label": r.group_label,
                "mean_value": r.mean_value,
                "unit": r.unit,
                "sample_size": r.sample_size,
                "notes": r.notes,
            }
            for r in rows
        ],
    }