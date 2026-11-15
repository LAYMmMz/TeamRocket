from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dev1_bridge import Dev1IntegrationBridge
from app.models.dev2_models import (
    BiologicalSample,
    ClinicalSampleChain,
    LaboratoryResult,
    new_uuid,
)
from app.schemas.dev2_schemas import LabResultCreate


class SamplesService:
    @staticmethod
    def ingest_lab_result(db: Session, payload: LabResultCreate) -> Dict[str, Any]:
        sample = BiologicalSample(
            event_id=new_uuid(),
            astronaut_id=payload.astronaut_id,
            sample_type=payload.sample_type,
            collected_at=payload.measured_at,
            processing_status="ANALYZED",
            source_type=payload.source_type,
            is_synthetic=payload.is_synthetic,
        )
        db.add(sample)
        db.flush()

        custody = ClinicalSampleChain(
            sample_id=sample.id,
            custody_event="ONBOARD_ASSAY_COMPLETE",
            responsible_person=payload.custody_actor,
            occurred_at=datetime.now(timezone.utc),
        )
        db.add(custody)

        test_upper = payload.test_code.upper()
        review_status = getattr(payload, "clinician_review_status", "UNREVIEWED")

        lab = LaboratoryResult(
            event_id=payload.event_id or new_uuid(),
            sample_id=sample.id,
            test_code=test_upper,
            result_value=payload.result_value,
            unit=payload.unit,
            assay_method=payload.assay_method,
            reviewer_status=review_status,
            measured_at=payload.measured_at,
            source_type=payload.source_type,
            is_synthetic=payload.is_synthetic,
        )
        db.add(lab)
        db.flush()

        abnormal = (
            (payload.reference_low is not None and payload.result_value < payload.reference_low)
            or (payload.reference_high is not None and payload.result_value > payload.reference_high)
        )

        interpretation_state = (
            "CLINICIAN_REVIEW_REQUIRED_NO_DIAGNOSIS"
            if abnormal
            else "WITHIN_REFERENCE_UNREVIEWED"
        )

        Dev1IntegrationBridge.enqueue_sync(
            db=db,
            event_id=lab.event_id,
            resource_type="laboratory_results",
            priority=2 if abnormal else 3,
            payload={
                "sample_id": sample.id,
                "lab_result_id": lab.id,
                "test_code": test_upper,
                "result_value": payload.result_value,
                "unit": payload.unit,
                "abnormal": abnormal,
                "interpretation_state": interpretation_state,
            },
        )

        alert_info = None
        if abnormal:
            alert_info = Dev1IntegrationBridge.emit_alert_and_optional_incident(
                db=db,
                rule_id=f"RULE-LAB-{test_upper}-REVIEW",
                rule_version="1.0.0",
                rule_approval_status="APPROVED",
                severity="ADVISORY",
                title=(
                    f"Abnormal {test_upper} result ({payload.result_value} {payload.unit}) "
                    "— clinician review required (no automated diagnosis)"
                ),
                evidence_refs=[f"laboratory_results:{lab.id}"],
                astronaut_id=payload.astronaut_id,
                open_incident=False,
                is_synthetic=payload.is_synthetic,
            )

        return {
            "id": lab.id,
            "lab_result_id": lab.id,
            "sample_id": sample.id,
            "astronaut_id": payload.astronaut_id,
            "test_code": test_upper,
            "result_value": payload.result_value,
            "unit": payload.unit,
            "abnormal": abnormal,
            "interpretation_state": interpretation_state,
            "reviewer_status": lab.reviewer_status,
            "clinician_review_status": lab.reviewer_status,
            "clinician_review_required": abnormal,
            "diagnosis_asserted": False,
            "alert": alert_info,
        }

    @staticmethod
    def list_lab_results(db: Session, astronaut_id: Optional[str] = None) -> List[Dict[str, Any]]:
        stmt = (
            select(LaboratoryResult, BiologicalSample)
            .join(BiologicalSample, LaboratoryResult.sample_id == BiologicalSample.id)
            .order_by(LaboratoryResult.measured_at.desc())
        )
        if astronaut_id:
            stmt = stmt.where(BiologicalSample.astronaut_id == astronaut_id)

        rows = db.execute(stmt).all()
        return [
            {
                "id": lab.id,
                "sample_id": sample.id,
                "astronaut_id": sample.astronaut_id,
                "sample_type": sample.sample_type,
                "test_code": lab.test_code,
                "result_value": lab.result_value,
                "unit": lab.unit,
                "assay_method": lab.assay_method,
                "reviewer_status": lab.reviewer_status,
                "clinician_review_status": lab.reviewer_status,
                "reviewed_by": lab.reviewed_by,
                "measured_at": lab.measured_at.isoformat(),
                "is_synthetic": lab.is_synthetic,
            }
            for lab, sample in rows
        ]

    @staticmethod
    def review_lab_result(
        db: Session,
        lab_result_id: str,
        reviewer_id: str,
        status: str = "CLINICIAN_REVIEWED",
    ) -> Dict[str, Any]:
        lab = db.get(LaboratoryResult, lab_result_id)
        if not lab:
            raise HTTPException(status_code=404, detail="Laboratory result not found.")
        lab.reviewer_status = status
        lab.reviewed_by = reviewer_id
        db.flush()
        return {
            "id": lab.id,
            "reviewer_status": lab.reviewer_status,
            "clinician_review_status": lab.reviewer_status,
            "reviewed_by": reviewer_id,
        }