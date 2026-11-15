from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import random
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.core.db import SessionLocal, get_shared_store, init_dev2_db
from app.models.dev2_models import (
    Base,
    BehavioralCheckin,
    BiologicalSample,
    BoneDensityResult,
    BoneScan,
    EcgRecord,
    EnvironmentalLabResult,
    EnvironmentalReading,
    EnvironmentalSample,
    ExerciseSession,
    FitnessAssessment,
    LaboratoryResult,
    LocalHealthAlert,
    LocalMedicalIncident,
    LocalSyncQueueItem,
    MedicalExamSchedule,
    MissionLocation,
    OcularAssessment,
    OcularResult,
    PersonalDoseRecord,
    RadiationEvent,
    SequencingRun,
    SleepSession,
    SymptomReport,
    VascularUltrasoundResult,
    VitalSign,
)

BASE_EPOCH = datetime(2026, 11, 15, 0, 0, 0, tzinfo=timezone.utc)
ANCHOR_TIME = BASE_EPOCH
CREW_IDS = ["CREW-01", "CREW-02", "CREW-03", "CREW-04"]


def _det_id(rng: random.Random, prefix: str) -> str:
    return f"{prefix}-{rng.getrandbits(64):016x}"


def _populate_dev1_store(store, rng: random.Random) -> None:
    """Populates Dev 1's encrypted SQLite Store so offline auth, rules, procedures & catalog work out of the box."""
    if store is None:
        return
    now_iso = BASE_EPOCH.isoformat()

    store.put(
        "missions",
        "DEMO-01",
        {
            "mission_id": "DEMO-01",
            "name": "Artemis Deep-Space Habitat Demo",
            "phase": "IN_FLIGHT_NORMAL",
            "is_synthetic": True,
            "source_type": "SIMULATED",
            "revision": 1,
            "created_at": now_iso,
            "updated_at": now_iso,
            "archived": False,
        },
        mission_id="DEMO-01",
        actor_id="seed-generator",
        immutable=False,
    )

    crew_meta = [
        ("CREW-01", "Cmdr. Elena Vance", "USR-CREW-01", "commander"),
        ("CREW-02", "Dr. Marcus Chen", "USR-FS-01", "flight_surgeon"),
        ("CREW-03", "Dr. Priya Nair", "USR-CREW-03", "mission_specialist"),
        ("CREW-04", "Lt. Samira Al-Mansoor", "USR-CREW-04", "flight_engineer"),
    ]
    for astro_id, name, user_id, duty_role in crew_meta:
        store.put(
            "astronauts",
            astro_id,
            {
                "astronaut_id": astro_id,
                "mission_id": "DEMO-01",
                "display_name": name,
                "user_id": user_id,
                "duty_role": duty_role,
                "is_synthetic": True,
                "source_type": "SIMULATED",
                "revision": 1,
                "created_at": now_iso,
                "updated_at": now_iso,
                "archived": False,
            },
            mission_id="DEMO-01",
            actor_id="seed-generator",
            immutable=False,
        )

    for idx in range(1, 11):
        dev_id = f"DEV-{idx:02d}"
        store.put(
            "devices",
            dev_id,
            {
                "device_id": dev_id,
                "mission_id": "DEMO-01",
                "name": f"Telemetry Sensor Unit {idx:02d}",
                "device_type": "BIOMONITOR" if idx <= 4 else "CABIN_ENV",
                "location": "HABITAT_CORE",
                "is_synthetic": True,
                "source_type": "SIMULATED",
                "revision": 1,
                "created_at": now_iso,
                "updated_at": now_iso,
                "archived": False,
            },
            mission_id="DEMO-01",
            actor_id="seed-generator",
            immutable=False,
        )

    # 20 DEMO-only condition catalog entries (Task 26 contract)
    for i in range(1, 21):
        cat_id = f"DEMO-IMM-{i:03d}"
        store.put(
            "condition_catalog",
            f"{cat_id}:v1:CODE-{i:03d}",
            {
                "catalog_id": cat_id,
                "version": 1,
                "code": f"CODE-{i:03d}",
                "title": f"Simulated Spaceflight Condition Reference #{i}",
                "description": "DEMO-only reference entry; not an official NASA IMM clinical diagnostic rule.",
                "source_name": "DEMO",
                "source_revision": "demo-2026.1",
                "source_type": "SIMULATED",
                "is_synthetic": True,
                "label": "SIMULATED",
            },
            actor_id="seed-generator",
            immutable=False,
        )

    # 12 inventory entries (Task 26 contract)
    for i in range(1, 13):
        lot_id = f"LOT-DEMO-{i:02d}"
        store.put(
            "inventory_lot",
            lot_id,
            {
                "lot_id": lot_id,
                "mission_id": "DEMO-01",
                "item_id": f"MED-ITEM-{i:02d}",
                "item_name": f"Simulated Medical Kit Item #{i}",
                "category": "medication" if i <= 6 else "consumable",
                "lot_number": f"B2026-{i:03d}",
                "quantity": 20 + i,
                "unit": "units",
                "expires_at": (BASE_EPOCH + timedelta(days=365)).isoformat(),
                "source_type": "SIMULATED",
                "is_synthetic": True,
            },
            mission_id="DEMO-01",
            actor_id="seed-generator",
            immutable=False,
        )

    # 8 neutral demo procedures (Task 13 contract)
    for i in range(1, 9):
        proc_id = f"PROC-DEMO-{i:02d}"
        store.put(
            "procedure",
            f"{proc_id}:v1",
            {
                "procedure_id": proc_id,
                "version": 1,
                "mission_id": "DEMO-01",
                "title": f"Simulated Operational Checklist #{i}",
                "mode": "DEMO",
                "source_type": "SIMULATED",
                "is_synthetic": True,
                "approval_state": "approved",
                "provenance": {
                    "source_title": "DEMO Procedural Fixture",
                    "source_revision": "v1",
                },
                "valid_from": (BASE_EPOCH - timedelta(days=1)).isoformat(),
                "expires_at": (BASE_EPOCH + timedelta(days=180)).isoformat(),
                "steps": [
                    {
                        "order": 1,
                        "title": "Verify Telemetry & Contact Flight Surgeon",
                        "instruction": "Confirm sensor quality and notify designated clinician for human review.",
                        "branches": [],
                    }
                ],
            },
            mission_id="DEMO-01",
            actor_id="seed-generator",
            immutable=False,
        )


def run_seed(
    db: Session,
    *,
    seed: int = 20261115,
    reset: bool = True,
    profile: str = "baseline",
    manifest_path: Optional[str] = None,
    shared_store: Any = None,
) -> Dict[str, Any]:
    env = os.getenv("APP_ENV", "development").strip().lower()
    if reset and env not in {"development", "dev", "test", "testing"}:
        raise PermissionError("Database reset is strictly forbidden outside development/test environments.")

    if reset:
        db.commit()
        db.expunge_all()
        conn = db.connection()
        Base.metadata.drop_all(bind=conn)
        Base.metadata.create_all(bind=conn)
        db.commit()

    rng = random.Random(seed)
    store = shared_store or db.info.get("store") or get_shared_store()
    _populate_dev1_store(store, rng)

    # Locations
    locations = [
        MissionLocation(location_code="HABITAT_CORE", zone_name="Habitat Core", location_type="HABITAT_MODULE", is_spe_shelter=False),
        MissionLocation(location_code="SHELTER_STORM_01", zone_name="Water-Wall Storm Shelter", location_type="STORM_SHELTER", is_spe_shelter=True),
        MissionLocation(location_code="AIRLOCK_01", zone_name="EVA Airlock", location_type="AIRLOCK", is_spe_shelter=False),
    ]
    db.add_all(locations)

    # 1. Vitals: 4 crew x 30 days x 24 timestamps x 3 metrics (HR, SPO2, RR) = 8,640 + BP 2/day/crew = 240 -> 8,880 total
    vitals_batch = []
    for astro in CREW_IDS:
        for day in range(30):
            for hour in range(24):
                ts = BASE_EPOCH - timedelta(days=29 - day, hours=23 - hour)
                hr = round(rng.uniform(58.0, 76.0), 1)
                spo2 = round(rng.uniform(96.5, 99.5), 1)
                rr = round(rng.uniform(12.0, 17.0), 1)
                for m_code, val, unit in [("HR", hr, "bpm"), ("SPO2", spo2, "%"), ("RR", rr, "breaths/min")]:
                    vitals_batch.append(
                        VitalSign(
                            id=_det_id(rng, "VIT"),
                            event_id=_det_id(rng, "EVT-VIT"),
                            astronaut_id=astro,
                            metric_code=m_code,
                            raw_value=val,
                            raw_unit=unit,
                            normalized_value=val,
                            normalized_unit=unit,
                            measured_at=ts,
                        )
                    )
            for bp_slot in (8, 20):
                ts_bp = BASE_EPOCH - timedelta(days=29 - day, hours=23 - bp_slot)
                bp_val = round(rng.uniform(110.0, 124.0), 1)
                vitals_batch.append(
                    VitalSign(
                        id=_det_id(rng, "VIT"),
                        event_id=_det_id(rng, "EVT-BP"),
                        astronaut_id=astro,
                        metric_code="BP_SYS",
                        raw_value=bp_val,
                        raw_unit="mmHg",
                        normalized_value=bp_val,
                        normalized_unit="mmHg",
                        measured_at=ts_bp,
                    )
                )
    db.bulk_save_objects(vitals_batch)

    # 2. ECG (4), Ocular (8/eye = 16), Vascular (8), Fitness (8), DXA (8 pre/postflight only)
    for i, astro in enumerate(CREW_IDS):
        db.add(
            EcgRecord(
                id=_det_id(rng, "ECG"),
                event_id=_det_id(rng, "EVT-ECG"),
                astronaut_id=astro,
                start_at=BASE_EPOCH - timedelta(hours=2),
                end_at=BASE_EPOCH - timedelta(hours=1, minutes=55),
                waveform_reference=f"s3://demo-waveforms/{astro}_ecg_01.wfdb",
                reviewed_interpretation="Normal sinus rhythm (SIMULATED)",
                reviewer_id="USR-FS-01",
                measured_at=BASE_EPOCH - timedelta(hours=2),
            )
        )
        for eye in ("LEFT", "RIGHT"):
            for k in range(2):
                assess = OcularAssessment(
                    id=_det_id(rng, "OCA"),
                    event_id=_det_id(rng, "EVT-OCA"),
                    astronaut_id=astro,
                    test_type="OCT_RNFL",
                    assessed_at=BASE_EPOCH - timedelta(days=15 * k),
                    measured_at=BASE_EPOCH - timedelta(days=15 * k),
                )
                db.add(assess)
                db.flush()
                db.add(
                    OcularResult(
                        id=_det_id(rng, "OCR"),
                        assessment_id=assess.id,
                        eye=eye,
                        scan_region="RNFL_GLOBAL",
                        metric_code="RNFL_THICKNESS",
                        value=round(98.0 + rng.uniform(-3.0, 3.0), 1),
                        unit="um",
                    )
                )
        for side in ("LEFT", "RIGHT"):
            db.add(
                VascularUltrasoundResult(
                    id=_det_id(rng, "VUS"),
                    event_id=_det_id(rng, "EVT-VUS"),
                    astronaut_id=astro,
                    vein="INTERNAL_JUGULAR",
                    side=side,
                    flow_pattern="NORMAL_PHASIC",
                    thrombus_finding="NONE_OBSERVED",
                    reviewed_by="USR-FS-01",
                    measured_at=BASE_EPOCH - timedelta(days=5),
                )
            )
        for f_idx in range(2):
            db.add(
                FitnessAssessment(
                    id=_det_id(rng, "FIT"),
                    event_id=_det_id(rng, "EVT-FIT"),
                    astronaut_id=astro,
                    test_type="VO2MAX",
                    metric_code="VO2_PEAK",
                    value=round(46.0 + f_idx * 0.5, 1),
                    unit="mL/kg/min",
                    protocol="CYCLE_ERGOMETER_GRADED",
                    assessed_at=BASE_EPOCH - timedelta(days=30 * f_idx),
                )
            )
        for phase in ("PREFLIGHT", "POSTFLIGHT"):
            scan = BoneScan(
                id=_det_id(rng, "DXA"),
                event_id=_det_id(rng, "EVT-DXA"),
                astronaut_id=astro,
                mission_phase=phase,
                scanned_at=BASE_EPOCH - timedelta(days=60 if phase == "PREFLIGHT" else 0),
                measured_at=BASE_EPOCH - timedelta(days=60 if phase == "PREFLIGHT" else 0),
            )
            db.add(scan)
            db.flush()
            db.add(
                BoneDensityResult(
                    id=_det_id(rng, "BMD"),
                    scan_id=scan.id,
                    bone_region="FEMORAL_NECK",
                    bmd_value=0.92 if phase == "PREFLIGHT" else 0.90,
                    unit="g/cm2",
                )
            )

    # 3. Daily Wellness: 120 sleep, 120 exercise, 24 symptoms, 20 behavioral check-ins
    for astro in CREW_IDS:
        for d in range(30):
            ts_d = BASE_EPOCH - timedelta(days=29 - d)
            db.add(
                SleepSession(
                    id=_det_id(rng, "SLP"),
                    event_id=_det_id(rng, "EVT-SLP"),
                    astronaut_id=astro,
                    start_at=ts_d - timedelta(hours=7),
                    end_at=ts_d,
                    duration_minutes=rng.randint(370, 440),
                )
            )
            db.add(
                ExerciseSession(
                    id=_det_id(rng, "EXE"),
                    event_id=_det_id(rng, "EVT-EXE"),
                    astronaut_id=astro,
                    exercise_type="ARED_RESISTANCE" if d % 2 == 0 else "CEVIS_CYCLE",
                    started_at=ts_d - timedelta(hours=10),
                    ended_at=ts_d - timedelta(hours=9),
                    duration_minutes=60,
                    workload_watts=165.0,
                    measured_at=ts_d - timedelta(hours=9),
                )
            )
        for s_idx in range(6):
            db.add(
                SymptomReport(
                    id=_det_id(rng, "SYM"),
                    event_id=_det_id(rng, "EVT-SYM"),
                    astronaut_id=astro,
                    symptom_code="MILD_CONGESTION",
                    severity="MILD",
                    onset_at=BASE_EPOCH - timedelta(days=s_idx * 4),
                    body_location="SINUS",
                    measured_at=BASE_EPOCH - timedelta(days=s_idx * 4),
                )
            )
        for b_idx in range(5):
            db.add(
                BehavioralCheckin(
                    id=_det_id(rng, "BEH"),
                    event_id=_det_id(rng, "EVT-BEH"),
                    astronaut_id=astro,
                    assessment_type="MOOD_FATIGUE",
                    score=round(rng.uniform(7.0, 9.0), 1),
                    visibility_classification="PRIVATE_CLINICAL",
                    measured_at=BASE_EPOCH - timedelta(days=b_idx * 5),
                )
            )

    # 4. Radiation & Cabin: 120 personal dose, 720 hourly CO2, 240 O2/pressure, 12 SPE context observations
    for astro in CREW_IDS:
        for d in range(30):
            db.add(
                PersonalDoseRecord(
                    id=_det_id(rng, "DOS"),
                    event_id=_det_id(rng, "EVT-DOS"),
                    astronaut_id=astro,
                    dosimeter_id=f"DOS-{astro}",
                    dose_quantity="EFFECTIVE_DOSE",
                    raw_value=0.45,
                    raw_unit="mSv",
                    normalized_value=0.45,
                    normalized_unit="mSv",
                    measured_at=BASE_EPOCH - timedelta(days=29 - d),
                )
            )
    for h in range(720):
        ts_h = BASE_EPOCH - timedelta(hours=719 - h)
        db.add(
            EnvironmentalReading(
                id=_det_id(rng, "ENV"),
                event_id=_det_id(rng, "EVT-CO2"),
                location_id="HABITAT_CORE",
                metric_code="PPCO2",
                raw_value=round(rng.uniform(2.1, 2.7), 2),
                raw_unit="mmHg",
                normalized_value=2.4,
                normalized_unit="mmHg",
                measured_at=ts_h,
            )
        )
    for p in range(240):
        ts_p = BASE_EPOCH - timedelta(hours=239 - p)
        db.add(
            EnvironmentalReading(
                id=_det_id(rng, "ENV"),
                event_id=_det_id(rng, "EVT-O2P"),
                location_id="HABITAT_CORE",
                metric_code="PPO2" if p % 2 == 0 else "PRESSURE",
                raw_value=160.0 if p % 2 == 0 else 101.3,
                raw_unit="mmHg" if p % 2 == 0 else "kPa",
                normalized_value=160.0 if p % 2 == 0 else 101.3,
                normalized_unit="mmHg" if p % 2 == 0 else "kPa",
                measured_at=ts_p,
            )
        )
    for spe_i in range(12):
        db.add(
            RadiationEvent(
                id=_det_id(rng, "SPE"),
                event_id=_det_id(rng, "EVT-SPE"),
                event_type="SOLAR_PARTICLE_BACKGROUND_WATCH",
                started_at=BASE_EPOCH - timedelta(days=spe_i * 2),
                status="ARCHIVED_WATCH",
                shelter_location_id="SHELTER_STORM_01",
                measured_at=BASE_EPOCH - timedelta(days=spe_i * 2),
            )
        )

    # 5. Biology: 24 bio samples, 32 lab results, 12 env samples, 16 env results, 4 sequencing runs
    for b_i in range(24):
        astro = CREW_IDS[b_i % 4]
        samp = BiologicalSample(
            id=_det_id(rng, "SMP"),
            event_id=_det_id(rng, "EVT-SMP"),
            astronaut_id=astro,
            sample_type="VENOUS_BLOOD" if b_i % 2 == 0 else "SALIVA",
            collected_at=BASE_EPOCH - timedelta(days=b_i),
        )
        db.add(samp)
        db.flush()
        db.add(
            LaboratoryResult(
                id=_det_id(rng, "LAB"),
                event_id=_det_id(rng, "EVT-LAB"),
                sample_id=samp.id,
                test_code="WBC_PANEL",
                result_value=6.2,
                unit="10^9/L",
                assay_method="BIO_ANALYZER_POC",
                measured_at=BASE_EPOCH - timedelta(days=b_i),
            )
        )
        if b_i < 8:
            db.add(
                LaboratoryResult(
                    id=_det_id(rng, "LAB"),
                    event_id=_det_id(rng, "EVT-LAB2"),
                    sample_id=samp.id,
                    test_code="D_DIMER",
                    result_value=0.32,
                    unit="ug/mL",
                    assay_method="ACTIS_IMMUNOASSAY",
                    measured_at=BASE_EPOCH - timedelta(days=b_i),
                )
            )
        if b_i < 4:
            db.add(
                SequencingRun(
                    id=_det_id(rng, "SEQ"),
                    event_id=_det_id(rng, "EVT-SEQ"),
                    sample_id=samp.id,
                    run_id=f"MINION-DEMO-{b_i + 1:02d}",
                    reads_count=48000 + b_i * 1200,
                    yield_bp=92_000_000,
                    qc_status="PASS",
                    source_file_ref=f"s3://demo-sequencing/run_{b_i + 1:02d}.fastq.gz",
                    measured_at=BASE_EPOCH - timedelta(days=b_i),
                )
            )

    for e_i in range(12):
        es = EnvironmentalSample(
            id=_det_id(rng, "ESM"),
            event_id=_det_id(rng, "EVT-ESM"),
            location_id="HABITAT_CORE",
            sample_type="POTABLE_WATER",
            sampling_method="MEMBRANE_FILTRATION_100ML",
            sample_quantity=100.0,
            sample_unit="mL",
            collected_at=BASE_EPOCH - timedelta(days=e_i * 2),
            measured_at=BASE_EPOCH - timedelta(days=e_i * 2),
        )
        db.add(es)
        db.flush()
        db.add(
            EnvironmentalLabResult(
                id=_det_id(rng, "ELR"),
                event_id=_det_id(rng, "EVT-ELR"),
                sample_id=es.id,
                test_code="TOTAL_COLIFORM",
                result_value=2.0,
                unit="CFU/100mL",
                standard_revision="DEMO-MICRO-V1",
                rule_approval_state="DEMO_ONLY",
                measured_at=BASE_EPOCH - timedelta(days=e_i * 2),
            )
        )
        if e_i < 4:
            db.add(
                EnvironmentalLabResult(
                    id=_det_id(rng, "ELR"),
                    event_id=_det_id(rng, "EVT-ELR2"),
                    sample_id=es.id,
                    test_code="HETEROTROPHIC_PLATE",
                    result_value=12.0,
                    unit="CFU/100mL",
                    standard_revision="DEMO-MICRO-V1",
                    rule_approval_state="DEMO_ONLY",
                    measured_at=BASE_EPOCH - timedelta(days=e_i * 2),
                )
            )

    # 6. Medical Ops & Sync QA: 8 incidents/alerts, 30 queued events (incl. 8 receipts, 5 retry, 4 duplicate replay)
    for idx in range(8):
        inc = LocalMedicalIncident(
            id=_det_id(rng, "INC"),
            astronaut_id=CREW_IDS[idx % 4],
            incident_type="ROUTINE_DEMO_DRILL",
            priority="MEDIUM",
            status="CLOSED",
        )
        db.add(inc)
        db.flush()
        db.add(
            LocalHealthAlert(
                id=_det_id(rng, "ALT"),
                incident_id=inc.id,
                astronaut_id=CREW_IDS[idx % 4],
                rule_id="RULE-DEMO-DRILL",
                rule_version="1.0.0",
                rule_approval_status="DEMO_ONLY",
                severity="ADVISORY",
                title=f"Baseline Drill Advisory #{idx + 1}",
                status="CLOSED",
            )
        )

    for q_i in range(30):
        status_val = "SYNCED" if q_i < 8 else ("RETRY" if q_i < 13 else "QUEUED")
        db.add(
            LocalSyncQueueItem(
                id=_det_id(rng, "SYN"),
                event_id=f"SYNC-BASELINE-{q_i + 1:03d}",
                resource_type="vital_signs",
                priority=1 if q_i < 4 else 5,
                payload={"seq": q_i + 1, "replay_case": q_i >= 26},
                status=status_val,
                attempt_count=2 if status_val == "RETRY" else (1 if status_val == "SYNCED" else 0),
                cloud_receipt_id=f"RCPT-SYNC-{q_i + 1:03d}" if status_val == "SYNCED" else None,
            )
        )

    for astro in CREW_IDS:
        db.add(
            MedicalExamSchedule(
                id=_det_id(rng, "EXM"),
                astronaut_id=astro,
                exam_type="OCT_RETINAL_SCAN",
                schedule_source="MED-TEMPLATE-INFLIGHT-V1",
                due_at=BASE_EPOCH + timedelta(days=15),
                completion_status="SCHEDULED",
            )
        )

    db.commit()

    counts = {
        "vital_signs": len(vitals_batch),
        "ecg_records": 4,
        "ocular_results_per_eye": 8,
        "vascular_ultrasound_results": 8,
        "fitness_assessments": 8,
        "bone_density_results": 8,
        "sleep_sessions": 120,
        "exercise_sessions": 120,
        "symptom_reports": 24,
        "behavioral_checkins": 20,
        "personal_dose_records": 120,
        "hourly_co2_readings": 720,
        "o2_and_pressure_readings": 240,
        "spe_context_observations": 12,
        "biological_samples": 24,
        "laboratory_results": 32,
        "environmental_samples": 12,
        "environmental_lab_results": 16,
        "sequencing_runs": 4,
        "demo_catalog_entries": 20,
        "inventory_lots": 12,
        "neutral_demo_procedures": 8,
        "incidents_and_alerts": 8,
        "sync_queue_events": 30,
    }
    checksum = hashlib.sha256(
        json.dumps({"seed": seed, "profile": profile, "counts": counts}, sort_keys=True).encode("utf-8")
    ).hexdigest()

    manifest = {
        "seed": seed,
        "profile": profile,
        "epoch_utc": BASE_EPOCH.isoformat(),
        "source_type": "SIMULATED",
        "is_synthetic": True,
        "counts": counts,
        "checksum_sha256": checksum,
    }

    if manifest_path:
        out = Path(manifest_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return manifest

def seed_baseline_dataset(
    db: Session,
    seed: int = 20261115,
    reset: bool = True,
    profile: str = "baseline",
    shared_store: Any = None,
    at_timestamp: datetime | None = None,
) -> dict[str, Any]:
    return run_seed(
        db=db,
        seed=seed,
        reset=reset,
        profile=profile,
        shared_store=shared_store,
    )

def main() -> None:
    parser = argparse.ArgumentParser(description="Deterministic NASA Health Monitoring Demo Seeder")
    parser.add_argument("--seed", type=int, default=20261115)
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--profile", type=str, default="baseline")
    parser.add_argument("--manifest", type=str, default="../docs/demo_manifest.json")
    args = parser.parse_args()

    init_dev2_db()
    with SessionLocal() as db:
        manifest = run_seed(
            db,
            seed=args.seed,
            reset=args.reset,
            profile=args.profile,
            manifest_path=args.manifest,
        )
        print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()