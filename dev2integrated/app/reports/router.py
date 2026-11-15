from __future__ import annotations

import csv
import io
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dev1_bridge import ActorContext, Dev1IntegrationBridge, MEDICAL_PRIVILEGED_ROLES, get_actor_context
from app.examinations.service import ExaminationsService
from app.models.dev2_models import (
    BehavioralCheckin,
    EnvironmentalReading,
    LaboratoryResult,
    LocalHealthAlert,
    PersonalDoseRecord,
    VitalSign,
)
from app.radiation.service import RadiationService
from app.vitals.service import VitalsService

router = APIRouter(prefix="/reports", tags=["reports & 7-dashboard feeds"])


def _build_report_payload(db: Session, astronaut_id: str, actor: ActorContext) -> dict:
    vitals = VitalsService.get_latest_vitals(db, astronaut_id)
    dose = RadiationService.get_astronaut_cumulative_dose(db, astronaut_id)
    exams = ExaminationsService.get_exam_schedule(db, astronaut_id)

    alerts = db.scalars(select(LocalHealthAlert).where(LocalHealthAlert.astronaut_id == astronaut_id)).all()
    env_rows = db.scalars(select(EnvironmentalReading).limit(10)).all()
    lab_rows = db.scalars(select(LaboratoryResult).limit(10)).all()

    # T28: Strip PRIVATE_CLINICAL behavioral records when requested by non-medical roles
    can_view_private = actor.role in MEDICAL_PRIVILEGED_ROLES or actor.astronaut_id == astronaut_id
    behavioral_items = []
    if can_view_private:
        b_rows = db.scalars(select(BehavioralCheckin).where(BehavioralCheckin.astronaut_id == astronaut_id)).all()
        behavioral_items = [
            {
                "id": b.id,
                "assessment_type": b.assessment_type,
                "score": b.score,
                "measured_at": b.measured_at.isoformat(),
                "badge": "SIMULATED" if b.is_synthetic else "VERIFIED",
            }
            for b in b_rows
        ]

    return {
        "astronaut_id": astronaut_id,
        "requested_by_role": actor.role,
        "private_behavioral_included": can_view_private,
        "dashboards": {
            "1_mission_medical_command": {
                "open_alerts": len([a for a in alerts if a.status == "OPEN"]),
                "badge": "SIMULATED",
            },
            "2_individual_astronaut_health": vitals,
            "3_clinical_examinations_and_recovery": exams,
            "4_radiation_and_environment": {
                "radiation": dose,
                "recent_environment_samples": len(env_rows),
            },
            "5_laboratory_and_immune_health": {
                "results_count": len(lab_rows),
                "unreviewed_count": len([r for r in lab_rows if r.reviewer_status == "UNREVIEWED"]),
            },
            "6_crew_self_assessment": {
                "behavioral_records": behavioral_items if can_view_private else "REDACTED_FOR_ROLE",
            },
            "7_ground_medical_review": {
                "sync_enabled": True,
                "classification": "PROTOTYPE_SYNTHETIC_REVIEW",
            },
        },
    }


@router.get("/{astronaut_id}")
def get_astronaut_report(
    astronaut_id: str,
    format: str = Query(default="json", pattern="^(json|csv)$"),
    db: Session = Depends(get_db),
    actor: ActorContext = Depends(get_actor_context),
):
    Dev1IntegrationBridge.record_audit(db, actor, f"EXPORT_REPORT_{format.upper()}", "reports", astronaut_id)
    report = _build_report_payload(db, astronaut_id, actor)
    if format == "json":
        return report

    # Role-safe CSV export (excludes unauthorized PRIVATE_CLINICAL rows)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["section", "metric", "value", "unit", "status_badge", "measured_at"])

    for metric, info in report["dashboards"]["2_individual_astronaut_health"]["vitals"].items():
        writer.writerow([
            "vitals",
            metric,
            info.get("value") if info.get("value") is not None else "MISSING",
            info.get("unit", ""),
            info.get("badge", info.get("status", "MISSING")),
            info.get("measured_at", ""),
        ])

    writer.writerow([
        "radiation",
        "cumulative_effective_dose",
        report["dashboards"]["4_radiation_and_environment"]["radiation"]["cumulative_effective_dose_msv"],
        "mSv",
        "RESEARCH_ONLY",
        "",
    ])

    if report["private_behavioral_included"]:
        for b in report["dashboards"]["6_crew_self_assessment"]["behavioral_records"]:
            writer.writerow(["behavioral_private", b["assessment_type"], b["score"], "score", b["badge"], b["measured_at"]])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={astronaut_id}_report.csv"},
    )