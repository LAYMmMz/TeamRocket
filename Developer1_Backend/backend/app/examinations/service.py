from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dev1_bridge import Dev1IntegrationBridge
from app.models.dev2_models import (
    BoneDensityResult,
    BoneScan,
    MedicalExamSchedule,
    OcularAssessment,
    OcularResult,
    VascularUltrasoundResult,
    new_uuid,
)
from app.schemas.dev2_schemas import BoneScanCreate, OcularAssessmentCreate, VascularUltrasoundCreate


class ExaminationsService:
    @staticmethod
    def get_exam_schedule(db: Session, astronaut_id: str, current_mission_phase: str = "IN_FLIGHT_NORMAL") -> Dict[str, Any]:
        # Task 20 & S08: Evaluate due/overdue schedules without ever fabricating missing test results
        now = datetime.now(timezone.utc)
        exams = db.scalars(
            select(MedicalExamSchedule)
            .where(MedicalExamSchedule.astronaut_id == astronaut_id)
            .order_by(MedicalExamSchedule.due_at.asc())
        ).all()

        items = []
        for ex in exams:
            due_utc = ex.due_at if ex.due_at.tzinfo else ex.due_at.replace(tzinfo=timezone.utc)
            if ex.completion_status in {"SCHEDULED", "DUE"} and due_utc < now:
                ex.completion_status = "OVERDUE"
            items.append(
                {
                    "id": ex.id,
                    "exam_type": ex.exam_type,
                    "schedule_source": ex.schedule_source,
                    "due_at": ex.due_at.isoformat(),
                    "completion_status": ex.completion_status,
                    "result_reference": ex.result_reference,
                }
            )
        db.flush()

        # Task 24 & S08: Explicitly surface that in-flight DXA BMD is unavailable (never fabricated)
        inflight_dxa_status = (
            "UNAVAILABLE_IN_FLIGHT_PRE_POST_ONLY"
            if current_mission_phase.startswith("IN_FLIGHT")
            else "AVAILABLE_GROUND_PROTOCOL"
        )
        return {
            "astronaut_id": astronaut_id,
            "mission_phase": current_mission_phase,
            "inflight_dxa_bmd_status": inflight_dxa_status,
            "fabricated_results_count": 0,
            "schedule": items,
        }

    @staticmethod
    def record_vascular_ultrasound(db: Session, payload: VascularUltrasoundCreate) -> Dict[str, Any]:
        # Task 22 & S06: Store LEFT and RIGHT internal jugular findings separately
        rec = VascularUltrasoundResult(
            event_id=payload.event_id or new_uuid(),
            astronaut_id=payload.astronaut_id,
            vein=payload.vein,
            side=payload.side,
            flow_pattern=payload.flow_pattern,
            thrombus_finding=payload.thrombus_finding,
            reviewed_by=payload.reviewed_by,
            reviewed_at=datetime.now(timezone.utc) if payload.reviewed_by else None,
            measured_at=payload.measured_at,
            source_type=payload.source_type,
            is_synthetic=payload.is_synthetic,
            verification_status="CLINICIAN_REVIEWED" if payload.reviewed_by else "UNREVIEWED",
        )
        db.add(rec)
        db.flush()

        alert_info = None
        if payload.flow_pattern != "NORMAL_PHASIC" or payload.thrombus_finding != "NONE_OBSERVED":
            alert_info = Dev1IntegrationBridge.emit_alert_and_optional_incident(
                db=db,
                rule_id="RULE-IJV-ULTRASOUND-REVIEW",
                rule_version="1.0.0",
                rule_approval_status="APPROVED",
                severity="WARNING",
                title=f"{payload.side} IJV ultrasound finding ({payload.flow_pattern} / {payload.thrombus_finding}) — clinician review required",
                evidence_refs=[f"vascular_ultrasound_results:{rec.id}"],
                astronaut_id=payload.astronaut_id,
                open_incident=False,
                is_synthetic=payload.is_synthetic,
            )

        return {
            "id": rec.id,
            "astronaut_id": rec.astronaut_id,
            "side": rec.side,
            "flow_pattern": rec.flow_pattern,
            "thrombus_finding": rec.thrombus_finding,
            "reviewed_by": rec.reviewed_by,
            "alert": alert_info,
        }

    @staticmethod
    def record_ocular_assessment(db: Session, payload: OcularAssessmentCreate) -> Dict[str, Any]:
        # Task 23: Store per-eye (LEFT/RIGHT) & per-region results; never compare OS against OD
        assessment = OcularAssessment(
            event_id=payload.event_id or new_uuid(),
            astronaut_id=payload.astronaut_id,
            test_type=payload.test_type,
            assessed_at=payload.assessed_at,
            report_reference=payload.report_reference,
            measured_at=payload.measured_at,
            source_type=payload.source_type,
            is_synthetic=payload.is_synthetic,
        )
        db.add(assessment)
        db.flush()

        saved_results = []
        for item in payload.results:
            row = OcularResult(
                assessment_id=assessment.id,
                eye=item.eye,
                scan_region=item.scan_region,
                metric_code=item.metric_code,
                value=item.value,
                unit=item.unit,
                interpretation=item.interpretation,
            )
            db.add(row)
            db.flush()
            saved_results.append({"id": row.id, "eye": row.eye, "scan_region": row.scan_region, "value": row.value})

        return {"assessment_id": assessment.id, "test_type": payload.test_type, "results": saved_results}

    @staticmethod
    def get_ocular_eye_trend(
        db: Session,
        astronaut_id: str,
        eye: str,
        scan_region: str = "RNFL_GLOBAL",
        metric_code: str = "RNFL_THICKNESS",
    ) -> Dict[str, Any]:
        eye_upper = eye.upper()
        if eye_upper not in {"LEFT", "RIGHT"}:
            raise HTTPException(status_code=422, detail="Eye must be explicitly LEFT or RIGHT.")

        rows = db.execute(
            select(OcularResult, OcularAssessment)
            .join(OcularAssessment, OcularResult.assessment_id == OcularAssessment.id)
            .where(
                OcularAssessment.astronaut_id == astronaut_id,
                OcularResult.eye == eye_upper,
                OcularResult.scan_region == scan_region,
                OcularResult.metric_code == metric_code,
            )
            .order_by(OcularAssessment.assessed_at.asc())
        ).all()

        if not rows:
            return {"astronaut_id": astronaut_id, "eye": eye_upper, "scan_region": scan_region, "status": "DATA_UNAVAILABLE", "points": []}

        return {
            "astronaut_id": astronaut_id,
            "eye": eye_upper,
            "scan_region": scan_region,
            "status": "AVAILABLE",
            "points": [
                {"assessed_at": a.assessed_at.isoformat(), "value": r.value, "unit": r.unit}
                for r, a in rows
            ],
        }

    @staticmethod
    def record_bone_scan(db: Session, payload: BoneScanCreate) -> Dict[str, Any]:
        # Task 24: Pre/postflight DXA only; strictly forbid fabricated in-flight BMD
        if payload.mission_phase == "INFLIGHT":
            raise HTTPException(
                status_code=422,
                detail="In-flight DXA BMD scans are unavailable onboard; fabricating in-flight BMD is prohibited.",
            )

        scan = BoneScan(
            event_id=payload.event_id or new_uuid(),
            astronaut_id=payload.astronaut_id,
            mission_phase=payload.mission_phase,
            scanned_at=payload.scanned_at,
            measured_at=payload.measured_at,
            source_type=payload.source_type,
            is_synthetic=payload.is_synthetic,
        )
        db.add(scan)
        db.flush()

        res = BoneDensityResult(
            scan_id=scan.id,
            bone_region=payload.bone_region,
            bmd_value=payload.bmd_value,
            unit=payload.unit,
            t_score=payload.t_score,
            z_score=payload.z_score,
        )
        db.add(res)
        db.flush()
        return {"scan_id": scan.id, "mission_phase": scan.mission_phase, "bone_region": res.bone_region, "bmd_value": res.bmd_value}

    @staticmethod
    def compare_dxa_same_region(db: Session, astronaut_id: str, bone_region: str) -> Dict[str, Any]:
        rows = db.execute(
            select(BoneDensityResult, BoneScan)
            .join(BoneScan, BoneDensityResult.scan_id == BoneScan.id)
            .where(BoneScan.astronaut_id == astronaut_id, BoneDensityResult.bone_region == bone_region)
            .order_by(BoneScan.scanned_at.asc())
        ).all()

        if not rows:
            return {"astronaut_id": astronaut_id, "bone_region": bone_region, "status": "DATA_UNAVAILABLE", "scans": []}

        preflight = next((r.bmd_value for r, s in rows if s.mission_phase == "PREFLIGHT"), None)
        postflight = next((r.bmd_value for r, s in reversed(rows) if s.mission_phase in {"POSTFLIGHT", "RECOVERY"}), None)
        delta_pct = round(((postflight - preflight) / preflight) * 100.0, 2) if (preflight and postflight) else None

        return {
            "astronaut_id": astronaut_id,
            "bone_region": bone_region,
            "status": "AVAILABLE",
            "preflight_bmd": preflight,
            "postflight_bmd": postflight,
            "percent_change": delta_pct,
            "inflight_bmd_fabricated": False,
        }