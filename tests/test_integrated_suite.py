from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.db import SessionLocal
from app.core.errors import AppError
from app.main import create_app
from app.seed.scenarios import execute_scenario
from app.seed.seed_demo import run_seed


def _make_test_client() -> TestClient:
    settings = Settings(
        environment="test",
        sqlite_path="./data/test_integrated_full.db",
        dev_auth_secret="test-secret-key-at-least-32-characters-long-1234",
        offline_grant_secret="offline-secret-key-at-least-32-characters-long-5678",
        allow_demo_rules=True,
    )
    return TestClient(create_app(settings))


def test_all_12_deterministic_scenarios_s01_to_s12():
    with _make_test_client() as client:
        with SessionLocal() as db:
            run_seed(db, seed=20261115, reset=True, shared_store=client.app.state.store)

            s01 = execute_scenario(db, "S01")
            assert not s01["vital_alert"]
            assert s01["env_alert"] is None

            s02 = execute_scenario(db, "S02")
            assert s02["activity_context"] != "RESTING"
            assert not s02["alert_generated"]

            s03 = execute_scenario(db, "S03")
            assert s03["incident_triggered"] is True
            assert s03["incident_id"] is not None
            assert s03["spo2_state"] not in {"VALID", "NORMAL"}

            s04 = execute_scenario(db, "S04")
            assert s04["rolling_1h_co2_mmhg"] > 3.0
            assert s04["correlated_incident_count"] == 1
            assert s04["causality_asserted"] is False

            s05 = execute_scenario(db, "S05")
            assert "REVIEW" in s05["interpretation_state"]
            assert "THROMBOSIS" not in s05["interpretation_state"]

            s06 = execute_scenario(db, "S06")
            assert s06["side"] == "LEFT"
            assert s06["alert"] is not None

            s07 = execute_scenario(db, "S07")
            assert s07["alert_id"] is not None
            assert len(s07["stale_dosimeter_crew"]) == 4

            s08 = execute_scenario(db, "S08")
            assert s08["fabricated_results_count"] == 0
            assert "UNAVAILABLE" in s08["inflight_dxa_bmd_status"]

            s09 = execute_scenario(db, "S09")
            assert s09["remediation_required"] is True
            assert s09["repeat_sampling_scheduled"] is True

            s10 = execute_scenario(db, "S10")
            assert s10["first_priority_event"] == "S10-EMERGENCY-SYM"
            assert s10["replay_synced_now"] == 0

            s11 = execute_scenario(db, "S11")
            assert s11["blocked"] is True

            s12 = execute_scenario(db, "S12")
            assert s12["forbidden"] is True


def test_nasa_endpoints_simulation_route_store_immutability_and_size_guard():
    with _make_test_client() as client:
        with SessionLocal() as db:
            run_seed(db, seed=20261115, reset=True, shared_store=client.app.state.store)

        # 1. NASA OSDR research endpoints remain strictly isolated reference data
        studies = client.get("/api/nasa/studies")
        assert studies.status_code == 200
        body = studies.json()
        assert body["classification"] == "NASA_OSDR_REFERENCE_DATA"
        assert body["is_clinical_threshold"] is False
        assert any(item["id"] == "OSD-104" for item in body["items"])

        obs = client.get("/api/nasa/studies/OSD-249/observations")
        assert obs.status_code == 200
        assert obs.json()["observations"][0]["metric_code"] == "SLEEP_DURATION_MINUTES"

        # 2. Simulation HTTP route executes S04 end-to-end
        sim_resp = client.post("/api/simulation/scenario", json={"scenario_id": "S04"})
        assert sim_resp.status_code == 200

        # 3. Dev 1 Store preserves immutable clinical evidence on conflicting overwrite
        store = client.app.state.store
        store.put("vital", "IMMUTABLE-VIT-01", {"hr": 68, "mission_id": "DEMO-01"}, immutable=True)
        with pytest.raises(AppError) as exc_info:
            store.put("vital", "IMMUTABLE-VIT-01", {"hr": 190, "mission_id": "DEMO-01"}, immutable=True)
        assert exc_info.value.status_code == 409
        assert len(store.conflicts(mission_id="DEMO-01")) >= 1

        # 4. Middleware blocks oversized (>2 MB) payloads with 413
        oversized = client.post(
            "/api/health",
            content=b"x" * (2 * 1024 * 1024 + 10),
            headers={"content-length": str(2 * 1024 * 1024 + 10)},
        )
        assert oversized.status_code == 413