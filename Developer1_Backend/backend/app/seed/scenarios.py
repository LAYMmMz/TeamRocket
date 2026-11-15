# backend/app/seed/scenarios.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dev1_bridge import ActorContext, Dev1IntegrationBridge
from app.environment.service import EnvironmentService
from app.examinations.service import ExaminationsService
from app.models.dev2_models import (
    LocalHealthAlert,
    LocalMedicalIncident,
    LocalSyncQueueItem,
    PersonalDoseRecord,
    VitalSign,
)
from app.radiation.service import RadiationService
from app.samples.service import SamplesService
from app.schemas.dev2_schemas import (
    EnvironmentalReadingCreate,
    EnvironmentalSampleCreate,
    ExerciseSessionCreate,
    LabResultCreate,
    SpeEventCreate,
    SymptomCreate,
    VascularUltrasoundCreate,
    VitalCreate,
)
from app.seed.seed_demo import ANCHOR_TIME, seed_baseline_dataset
from app.vitals.service import VitalsService
from app.wellness.service import WellnessService


def execute_scenario(
    db: Session,
    scenario_id: str,
    seed: int = 20261115,
    at_timestamp: datetime | None = None,
    shared_store: Any = None,
) -> Dict[str, Any]:
    """
    Deterministic replay engine for scenarios S01 through S12.
    Always resets cleanly to `seed` first so scenario outcomes are 100% repeatable.
    """
    seed_baseline_dataset(
        db=db,
        seed=seed,
        reset=True,
        shared_store=shared_store,
        at_timestamp=at_timestamp,
    )
    now = at_timestamp or datetime.now(timezone.utc)

    if scenario_id == "S01":
        # Normal vitals & environment -> zero inappropriate alerts
        vital_out = VitalsService.ingest_vital(
            db,
            VitalCreate(
                event_id="S01-VIT-HR",
                astronaut_id="CREW-01",
                metric_code="HR",
                value=66.0,
                unit="bpm",
                measured_at=now,
            ),
        )
        env_out = EnvironmentService.ingest_reading(
            db,
            EnvironmentalReadingCreate(
                event_id="S01-ENV-CO2",
                location_id="HAB-CORE",
                metric_code="PPCO2",
                value=2.0,
                unit="mmHg",
                measured_at=now,
            ),
        )
        return {"scenario": "S01", "vital_alert": vital_out.alert_generated, "env_alert": env_out["alert"]}

    if scenario_id == "S02":
        # High HR during workout -> activity context applied, no resting tachycardia alert
        VitalsService.log_exercise_session(
            db,
            ExerciseSessionCreate(
                event_id="S02-EXE-1",
                astronaut_id="CREW-01",
                exercise_type="CEVIS_CYCLE",
                started_at=now - timedelta(minutes=15),
                ended_at=now + timedelta(minutes=15),
                duration_minutes=30.0,
                workload_watts=180.0,
                measured_at=now - timedelta(minutes=15),
            ),
        )
        vital_out = VitalsService.ingest_vital(
            db,
            VitalCreate(
                event_id="S02-VIT-HR",
                astronaut_id="CREW-01",
                metric_code="HR",
                value=148.0,
                unit="bpm",
                measured_at=now,
            ),
        )
        return {
            "scenario": "S02",
            "activity_context": vital_out.activity_context,
            "alert_generated": vital_out.alert_generated,
        }

    if scenario_id == "S03":
        # Serious breathing symptom + missing SpO2 -> immediate local incident, no fabricated SpO2
        db.query(VitalSign).filter(VitalSign.astronaut_id == "CREW-02", VitalSign.metric_code == "SPO2").delete()
        db.flush()
        sym_res = WellnessService.create_symptom_report(
            db,
            SymptomCreate(
                event_id="S03-SYM-1",
                astronaut_id="CREW-02",
                symptom_code="DYSPNEA",
                severity=8.5,
                onset_at=now,
                measured_at=now,
                body_location="CHEST",
            ),
        )
        vitals_snapshot = VitalsService.get_latest_vitals(db, "CREW-02")
        return {
            "scenario": "S03",
            "incident_triggered": sym_res["incident_triggered"],
            "incident_id": sym_res["incident_id"],
            "spo2_state": vitals_snapshot["vitals"]["SPO2"]["status"],
        }

    if scenario_id == "S04":
        # Time-window CO2 exceedance + headache -> bundled under ONE linked-evidence incident without asserting causality
        for i in range(4):
            env_res = EnvironmentService.ingest_reading(
                db,
                EnvironmentalReadingCreate(
                    event_id=f"S04-CO2-{i}",
                    location_id="HAB-CORE",
                    metric_code="PPCO2",
                    value=4.8,
                    unit="mmHg",
                    measured_at=now - timedelta(minutes=(3 - i) * 10),
                    rule_approval_state="DEMO_ONLY",
                ),
            )
        sym_res = WellnessService.create_symptom_report(
            db,
            SymptomCreate(
                event_id="S04-SYM-HEADACHE",
                astronaut_id="CREW-01",
                symptom_code="HEADACHE",
                severity=6.0,
                onset_at=now,
                measured_at=now,
                body_location="HEAD",
            ),
        )
        open_incidents = db.scalars(
            select(LocalMedicalIncident).where(
                LocalMedicalIncident.status == "OPEN",
                LocalMedicalIncident.incident_type == "CO2_AND_HEADACHE_CORRELATED_REVIEW",
            )
        ).all()
        return {
            "scenario": "S04",
            "rolling_1h_co2_mmhg": env_res["rolling_1h_average"],
            "correlated_incident_count": len(open_incidents),
            "causality_asserted": open_incidents[0].causality_asserted if open_incidents else False,
            "symptom_incident_id": sym_res["incident_id"],
        }

    if scenario_id == "S05":
        # Unreviewed D-dimer -> clinician review only, NOT thrombosis diagnosis
        lab_res = SamplesService.ingest_lab_result(
            db,
            LabResultCreate(
                event_id="S05-LAB-DDIMER",
                astronaut_id="CREW-03",
                sample_type="BLOOD",
                custody_actor="CREW-02",
                test_code="D_DIMER",
                result_value=820.0,
                unit="ng/mL",
                assay_method="BIO_ANALYZER",
                reference_low=0.0,
                reference_high=500.0,
                clinician_review_status="UNREVIEWED",
                measured_at=now,
            ),
        )
        return {
            "scenario": "S05",
            "interpretation_state": lab_res["interpretation_state"],
            "alert_generated": lab_res["alert"] is not None,
        }

    if scenario_id == "S06":
        # Left-side internal jugular ultrasound finding -> separate sided record + clinician review action
        us_res = ExaminationsService.record_vascular_ultrasound(
            db,
            VascularUltrasoundCreate(
                event_id="S06-US-LEFT",
                astronaut_id="CREW-03",
                vein="INTERNAL_JUGULAR",
                side="LEFT",
                flow_pattern="STAGNANT",
                thrombus_finding="SUSPECTED_REVIEW_REQUIRED",
                reviewed_by="USR-FS-01",
                measured_at=now,
            ),
        )
        return {"scenario": "S06", "side": us_res["side"], "alert": us_res["alert"]}

    if scenario_id == "S07":
        # SPE event + stale dosimeter -> warning in demo/approved mode, stale flag & compatible units
        stale_cutoff = now - timedelta(hours=12)
        for rec in db.scalars(select(PersonalDoseRecord)).all():
            rec.measured_at = stale_cutoff
            rec.quality_status = "STALE"
        db.flush()

        spe_res = RadiationService.trigger_spe_event(
            db,
            SpeEventCreate(
                event_id="S07-SPE-1",
                mission_id="DEMO-01",
                started_at=now,
                measured_at=now,
                shelter_location_id="HAB-CORE",
                rule_approval_state="DEMO_ONLY",
            ),
            astronaut_ids=["CREW-01", "CREW-02", "CREW-03", "CREW-04"],
        )
        return {
            "scenario": "S07",
            "rule_approval_state": spe_res["rule_approval_state"],
            "stale_dosimeter_crew": spe_res["stale_dosimeter_crew"],
            "alert_id": spe_res["alert_id"],
        }

    if scenario_id == "S08":
        # OCT due + no in-flight DXA -> reminders, no fabricated results
        sched = ExaminationsService.get_exam_schedule(db, "CREW-01", current_mission_phase="IN_FLIGHT_NORMAL")
        return {
            "scenario": "S08",
            "inflight_dxa_bmd_status": sched["inflight_dxa_bmd_status"],
            "fabricated_results_count": sched["fabricated_results_count"],
            "schedule": sched["schedule"],
        }

    if scenario_id == "S09":
        # Water culture flag -> method-aware interpretation (CFU/100mL) + remediation & re-sampling request
        micro_res = EnvironmentService.ingest_microbiology_sample(
            db,
            EnvironmentalSampleCreate(
                event_id="S09-WATER-1",
                location_id="HAB-CORE",
                sample_type="POTABLE_WATER",
                sampling_method="MEMBRANE_FILTRATION_100ML",
                sample_quantity=100.0,
                sample_unit="mL",
                test_code="TOTAL_BACTERIA_CFU",
                result_value=145.0,
                result_unit="CFU/100mL",
                rule_approval_state="DEMO_ONLY",
                measured_at=now,
            ),
        )
        return {
            "scenario": "S09",
            "remediation_required": micro_res["remediation_required"],
            "remediation_action": micro_res["remediation_action"],
            "repeat_sampling_scheduled": micro_res["repeat_sampling_scheduled"],
        }

    if scenario_id == "S10":
        # Earth disconnect -> emergency incident queued locally in SQLite -> reconnect -> exactly-once priority sync
        offline_status = Dev1IntegrationBridge.flush_sync_queue_idempotent(db, earth_connected=False)
        WellnessService.create_symptom_report(
            db,
            SymptomCreate(
                event_id="S10-EMERGENCY-SYM",
                astronaut_id="CREW-04",
                symptom_code="CHEST_PAIN",
                severity=9.0,
                onset_at=now,
                measured_at=now,
                body_location="CHEST",
            ),
        )
        # Re-enqueue duplicate event_id to verify idempotency
        Dev1IntegrationBridge.enqueue_sync(db, "S10-EMERGENCY-SYM", "symptom_reports", 1, {"dup": True})
        reconnect_first = Dev1IntegrationBridge.flush_sync_queue_idempotent(db, earth_connected=True)
        reconnect_replay = Dev1IntegrationBridge.flush_sync_queue_idempotent(db, earth_connected=True)
        return {
            "scenario": "S10",
            "offline_pending": offline_status["pending_in_sqlite"],
            "first_priority_event": reconnect_first["ordered_event_ids"][0],
            "replay_synced_now": reconnect_replay["synced_now"],
        }

    if scenario_id == "S11":
        # Unapproved/expired operational rule blocked
        blocked = False
        reason = ""
        try:
            Dev1IntegrationBridge.emit_alert_and_optional_incident(
                db=db,
                rule_id="RULE-EXPIRED-PROTOCOL",
                rule_version="0.9.0",
                rule_approval_status="EXPIRED",
                severity="WARNING",
                title="Should be blocked",
                evidence_refs=[],
            )
        except HTTPException as exc:
            blocked = exc.status_code == 422
            reason = exc.detail
        return {"scenario": "S11", "blocked": blocked, "reason": reason}

    if scenario_id == "S12":
        # Unauthorized behavioral check-in access -> 403 forbidden + audited
        forbidden = False
        try:
            WellnessService.get_wellness_summary(
                db=db,
                astronaut_id="CREW-01",
                actor=ActorContext(user_id="USR-ENG-99", role="FLIGHT_ENGINEER", astronaut_id="CREW-03"),
            )
        except HTTPException as exc:
            forbidden = exc.status_code == 403
        return {"scenario": "S12", "forbidden": forbidden}

    raise HTTPException(status_code=400, detail=f"Unknown scenario_id: {scenario_id}")
    
run_scenario = execute_scenario

# Compatibility with the committed simulation router.
run_scenario = execute_scenario
