from __future__ import annotations

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dev1_bridge import ActorContext, get_actor_context
from app.models.dev2_models import (
    BiologicalSample,
    ClinicalSampleChain,
    LaboratoryResult,
    SequencingRun,
    new_uuid,
)

router = APIRouter(prefix="/samples", tags=["laboratory & sequencing"])


class SampleCreate(BaseModel):
    event_id: Optional[str] = None
    astronaut_id: str
    sample_type: str
    collected_at: datetime
    collector_id: str
    source_type: str = "SIMULATED"
    is_synthetic: bool = True


class CustodyTransferCreate(BaseModel):
    custody_event: str
    responsible_person: str


class LabResultCreate(BaseModel):
    event_id: Optional[str] = None
    sample_id: str
    test_code: str
    result_value: float
    unit: str
    assay_method: str
    measured_at: datetime
    source_type: str = "SIMULATED"
    is_synthetic: bool = True


class MinionRunCreate(BaseModel):
    event_id: Optional[str] = None
    sample_id: str
    run_id: str
    reads_count: int
    yield_bp: int
    qc_status: str
    source_file_ref: str
    measured_at: datetime
    source_type: str = "SIMULATED"
    is_synthetic: bool = True


@router.post("", status_code=201)
def register_sample(
    payload: SampleCreate,
    db: Session = Depends(get_db),
    _actor: ActorContext = Depends(get_actor_context),
):
    sample = BiologicalSample(
        event_id=payload.event_id or new_uuid(),
        astronaut_id=payload.astronaut_id,
        sample_type=payload.sample_type,
        collected_at=payload.collected_at,
        source_type=payload.source_type,
        is_synthetic=payload.is_synthetic,
    )
    db.add(sample)
    db.flush()
    db.add(
        ClinicalSampleChain(
            sample_id=sample.id,
            custody_event="COLLECTED",
            responsible_person=payload.collector_id,
            occurred_at=payload.collected_at,
        )
    )
    db.flush()
    return {"id": sample.id, "sample_type": sample.sample_type, "chain_events": 1}


@router.post("/{sample_id}/custody", status_code=201)
def add_custody_event(
    sample_id: str,
    payload: CustodyTransferCreate,
    db: Session = Depends(get_db),
    _actor: ActorContext = Depends(get_actor_context),
):
    ev = ClinicalSampleChain(
        sample_id=sample_id,
        custody_event=payload.custody_event,
        responsible_person=payload.responsible_person,
    )
    db.add(ev)
    db.flush()
    return {"id": ev.id, "sample_id": sample_id, "custody_event": ev.custody_event}


@router.post("/lab-results", status_code=201)
def record_lab_result(
    payload: LabResultCreate,
    db: Session = Depends(get_db),
    _actor: ActorContext = Depends(get_actor_context),
):
    res = LaboratoryResult(
        event_id=payload.event_id or new_uuid(),
        sample_id=payload.sample_id,
        test_code=payload.test_code,
        result_value=payload.result_value,
        unit=payload.unit,
        assay_method=payload.assay_method,
        reviewer_status="UNREVIEWED",
        measured_at=payload.measured_at,
        source_type=payload.source_type,
        is_synthetic=payload.is_synthetic,
    )
    db.add(res)
    db.flush()
    return {
        "id": res.id,
        "test_code": res.test_code,
        "reviewer_status": "UNREVIEWED",
        "automated_diagnosis": False,
    }


@router.post("/sequencing-runs", status_code=201)
def record_minion_run(
    payload: MinionRunCreate,
    db: Session = Depends(get_db),
    _actor: ActorContext = Depends(get_actor_context),
):
    """T21: MinION sequencing QC & provenance; never outputs automated pathogen diagnosis."""
    run = SequencingRun(
        event_id=payload.event_id or new_uuid(),
        sample_id=payload.sample_id,
        run_id=payload.run_id,
        reads_count=payload.reads_count,
        yield_bp=payload.yield_bp,
        qc_status=payload.qc_status,
        source_file_ref=payload.source_file_ref,
        reviewer_status="PENDING_MANUAL_REVIEW",
        automated_pathogen_diagnosis=False,
        measured_at=payload.measured_at,
        source_type=payload.source_type,
        is_synthetic=payload.is_synthetic,
    )
    db.add(run)
    db.flush()
    return {
        "id": run.id,
        "run_id": run.run_id,
        "qc_status": run.qc_status,
        "reviewer_status": run.reviewer_status,
        "automated_pathogen_diagnosis": False,
    }


@router.get("/{sample_id}/chain")
def get_custody_chain(
    sample_id: str,
    db: Session = Depends(get_db),
    _actor: ActorContext = Depends(get_actor_context),
):
    rows = db.scalars(
        select(ClinicalSampleChain)
        .where(ClinicalSampleChain.sample_id == sample_id)
        .order_by(ClinicalSampleChain.occurred_at.asc())
    ).all()
    return {
        "sample_id": sample_id,
        "chain": [
            {
                "custody_event": r.custody_event,
                "responsible_person": r.responsible_person,
                "occurred_at": r.occurred_at.isoformat(),
            }
            for r in rows
        ],
    }