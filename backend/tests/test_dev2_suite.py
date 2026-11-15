from __future__ import annotations

from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.seed.seed_demo import run_seed
from app.core.db import SessionLocal


def _make_test_client() -> TestClient:
    settings = Settings(
        environment="test",
        sqlite_path="./data/test_integrated.db",
        dev_auth_secret="test-secret-key-at-least-32-characters-long-1234",
        offline_grant_secret="offline-secret-key-at-least-32-characters-long-5678",
        allow_demo_rules=True,
    )
    app = create_app(settings)
    return TestClient(app)


def test_merged_app_seed_symptoms_rbac_reports_and_guardrails():
    with _make_test_client() as client:
        # 1. Health endpoint reports unified SQLite schema & sync status
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        # 2. Deterministic seed populates exact Mandatory Synthetic Dataset Contract counts & Dev 1 Store
        with SessionLocal() as db:
            manifest = run_seed(
                db,
                seed=20261115,
                reset=True,
                profile="baseline",
                shared_store=client.app.state.store,
            )
        assert manifest["counts"]["vital_signs"] == 8880
        assert manifest["counts"]["hourly_co2_readings"] == 720
        assert manifest["counts"]["sync_queue_events"] == 30
        assert client.app.state.store.get("missions", "DEMO-01") is not None

        # 3. Serious symptom with ZERO sensor readings triggers immediate incident in both Dev 2 & Dev 1 Store (T10 / S03)
        now_iso = datetime.now(timezone.utc).isoformat()
        sym_resp = client.post(
            "/symptoms",
            json={
                "astronaut_id": "CREW-01",
                "mission_id": "DEMO-01",
                "symptom_code": "SEVERE_DYSPNEA",
                "severity": "CRITICAL",
                "onset_at": now_iso,
                "body_location": "CHEST",
                "measured_at": now_iso,
            },
        )
        assert sym_resp.status_code == 201
        assert sym_resp.json()["incident_id"] is not None

        # 4. Gravity transition & reaction check never auto-approves EVA (T17)
        grav_resp = client.post(
            "/wellness/gravity-transitions",
            json={"from_g": 0.0, "to_g": 0.16, "occurred_at": now_iso},
        )
        assert grav_resp.status_code == 201
        assert grav_resp.json()["eva_clearance_status"] == "PENDING_HUMAN_REVIEW"
        assert grav_resp.json()["autonomous_eva_decision"] is False

        # 5. MinION sequencing logs QC without automated pathogen diagnosis (T21)
        samp = client.post(
            "/samples",
            json={
                "astronaut_id": "CREW-01",
                "sample_type": "SWAB",
                "collected_at": now_iso,
                "collector_id": "CREW-02",
            },
        ).json()
        seq = client.post(
            "/samples/sequencing-runs",
            json={
                "sample_id": samp["id"],
                "run_id": "MINION-TEST-99",
                "reads_count": 51000,
                "yield_bp": 95000000,
                "qc_status": "PASS",
                "source_file_ref": "s3://demo/run99.fastq",
                "measured_at": now_iso,
            },
        )
        assert seq.status_code == 201
        assert seq.json()["automated_pathogen_diagnosis"] is False

        # 6. Role-safe reports redact PRIVATE_CLINICAL behavioral data for non-medical roles (T28 / S12)
        rep_crew = client.get(
            "/reports/CREW-01?format=json",
            headers={"X-User-Id": "USR-CREW-03", "X-User-Role": "CREW", "X-Astronaut-Id": "CREW-03"},
        )
        assert rep_crew.status_code == 200
        assert rep_crew.json()["private_behavioral_included"] is False

        rep_fs = client.get(
            "/reports/CREW-01?format=csv",
            headers={"X-User-Id": "USR-FS-01", "X-User-Role": "FLIGHT_SURGEON"},
        )
        assert rep_fs.status_code == 200
        assert "behavioral_private" in rep_fs.text