# backend/app/reports/service.py
from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dev1_bridge import ActorContext, Dev1IntegrationBridge, MEDICAL_PRIVILEGED_ROLES
from app.examinations.service import ExaminationsService
from app.models.dev2_models import Astronaut, BehavioralCheckin, LocalHealthAlert, LocalMedicalIncident
from app.radiation.service import RadiationService
from app.vitals.service import VitalsService


class ReportsService:
    @staticmethod
    def build_astronaut_report(db: Session, astronaut_id: str, actor: ActorContext) -> Dict[str, Any]:
        astro = db.scalars(select(Astronaut).where(Astronaut.id == astronaut_id)).first()
        vitals = VitalsService.get_latest_vitals(db, astronaut_id)
        radiation = RadiationService.get_astronaut_cumulative_dose(db, astronaut_id)
        schedule = ExaminationsService.get_exam_schedule(db, astronaut_id)

        alerts = db.scalars(
            select(LocalHealthAlert).where(LocalHealthAlert.astronaut_id == astronaut_id)
        ).all()
        incidents = db.scalars(
            select(LocalMedicalIncident).where(LocalMedicalIncident.astronaut_id == astronaut_id)
        ).all()

        # Role-safe redaction: non-medical roles never receive confidential behavioral check-in contents
        can_view_behavioral = actor.role in MEDICAL_PRIVILEGED_ROLES or actor.astronaut_id == astronaut_id
        behavioral_section: Dict[str, Any]
        if can_view_behavioral:
            checkins = db.scalars(
                select(BehavioralCheckin).where(BehavioralCheckin.astronaut_id == astronaut_id)
            ).all()
            behavioral_section = {
                "access": "AUTHORIZED",
                "count": len(checkins),
                "badge": "SIMULATED",
            }
        else:
            behavioral_section = {
                "access": "REDACTED_BY_RBAC",
                "count": None,
                "badge": "RESTRICTED",
            }

        Dev1IntegrationBridge.record_audit(
            db=db,
            actor=actor,
            action="EXPORT_ASTRONAUT_REPORT",
            resource_type="reports",
            resource_id=astronaut_id,
            outcome="ALLOWED",
        )

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "astronaut_id": astronaut_id,
            "display_name": astro.display_name if astro else astronaut_id,
            "source_badge": "SIMULATED" if (astro and astro.is_synthetic) else "VERIFIED",
            "vitals_summary": vitals["vitals"],
            "radiation_summary": radiation,
            "examination_schedule": schedule,
            "behavioral_health": behavioral_section,
            "active_alerts_count": len(alerts),
            "open_incidents_count": len(incidents),
        }

    @staticmethod
    def render_csv(report: Dict[str, Any]) -> str:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["astronaut_id", "section", "metric", "value", "unit", "status_or_badge"])
        astro_id = report["astronaut_id"]

        for metric, data in report["vitals_summary"].items():
            writer.writerow([astro_id, "VITALS", metric, data.get("value"), data.get("unit"), data.get("status")])

        rad = report["radiation_summary"]
        writer.writerow([
            astro_id,
            "RADIATION",
            "CUMULATIVE_EFFECTIVE_DOSE",
            rad["cumulative_effective_dose_msv"],
            "mSv",
            rad["reference_gating"],
        ])

        beh = report["behavioral_health"]
        writer.writerow([astro_id, "BEHAVIORAL", "CHECKIN_COUNT", beh["count"], "count", beh["access"]])
        return buf.getvalue()