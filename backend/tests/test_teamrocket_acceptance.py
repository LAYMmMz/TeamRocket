"""TeamRocket offline-first acceptance tests, test data only.

Run: python run_teamrocket_tests.py

The suite NEVER uses a real Supabase account or the user's data/offline.db.
HTTP tests run FastAPI in-process with a new temporary encrypted SQLite database.
The S04 and S05 scenarios are reported as SKIP because the provided Dev2 package
contains descriptors, not the necessary executable medical-domain workflows.
"""
import json
import os
import tempfile
import unittest
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from scripts.seed_demo import generate, SCENARIO_DESCRIPTIONS

MISSION = "DEMO-01"
T0 = datetime(2026, 11, 1, 12, tzinfo=timezone.utc)


def domain_event(domain, data, suffix="01", **changes):
    payload = {
        "event_id": f"test-{domain}-{suffix}", "mission_id": MISSION,
        "astronaut_id": "CREW-01", "source_type": "SIMULATED",
        "is_synthetic": True, "measured_at": T0.isoformat(),
        "received_at": (T0 + timedelta(minutes=1)).isoformat(),
        "quality": "VALID", "verification": "UNVERIFIED",
        "source_reference": "TeamRocket acceptance fixture",
        "source_revision": "test-v1", "data": data,
    }
    payload.update(changes)
    return payload


def reading(metric="heart_rate", value=75, event_id="read-001", **changes):
    payload = {
        "event_id": event_id, "mission_id": MISSION,
        "astronaut_id": "CREW-01", "device_id": None,
        "metric": metric, "value": value,
        "unit": {
            "heart_rate": "bpm", "spo2": "%",
            "respiratory_rate": "breaths/min",
            "systolic_bp": "mmHg", "diastolic_bp": "mmHg",
            "temperature": "Cel",
        }.get(metric, "bpm"),
        "metadata": {}, "source_type": "SIMULATED",
        "is_synthetic": True, "measured_at": T0.isoformat(),
        "quality": "VALID", "verification": "UNVERIFIED",
        "source_reference": "TeamRocket acceptance fixture",
        "source_revision": "test-v1",
    }
    payload.update(changes)
    return payload


class IsolatedAPI(unittest.TestCase):
    """Each test gets its own real FastAPI application and disposable encrypted DB."""

    def setUp(self):
        from app.core.config import Settings
        from app.main import create_app
        from app.auth.dependencies import issue_development_token
        self.create_app = create_app
        self.issue_development_token = issue_development_token
        self.tmp = tempfile.TemporaryDirectory(prefix="teamrocket_test_")
        self.addCleanup(self.tmp.cleanup)
        self.settings = Settings()
        self.settings.environment = "test"
        self.settings.sqlite_path = str(Path(self.tmp.name) / "offline.db")
        self.settings.encryption_key = Fernet.generate_key().decode()
        self.settings.dev_auth_secret = "test-auth-secret-with-at-least-32-chars-keep-private"
        self.settings.offline_grant_secret = "test-offline-grant-secret-32-chars-keep-private"
        self.settings.sync_rpc_url = ""
        self.settings.sync_access_token = ""
        self.settings.supabase_url = ""
        self.settings.supabase_anon_key = ""
        self.settings.allow_demo_rules = False
        self.settings.cors_origins = ["http://localhost:5173"]
        self.app = create_app(self.settings)
        self.client = TestClient(self.app, raise_server_exceptions=True)
        self.client.__enter__()
        self.addCleanup(lambda: self.client.__exit__(None, None, None))
        self.admin = self._headers(["admin"])
        self.crew = self._headers(["crew"])
        self.researcher = self._headers(["researcher"])
        self._mission()

    def _headers(self, roles, missions=None):
        token = self.issue_development_token(
            self.settings, "qa-" + roles[0], roles,
            missions or [MISSION], ttl_minutes=60,
        )
        return {"Authorization": "Bearer " + token}

    def _mission(self):
        r = self.client.post("/api/missions", headers=self.admin, json={
            "mission_id": MISSION, "name": "QA synthetic mission",
            "source_type": "SIMULATED", "is_synthetic": True,
            "verification": "UNVERIFIED",
        })
        self.assertEqual(r.status_code, 201, r.text)

    def _post_domain(self, domain, data, *, suffix="01", headers=None, **changes):
        return self.client.post(
            "/api/domain2/" + domain,
            headers=headers or self.admin,
            json=domain_event(domain, data, suffix, **changes),
        )

    def _domain_created(self, domain, data, *, suffix="01"):
        r = self._post_domain(domain, data, suffix=suffix)
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()

    def test_api_01_health_and_local_schema(self):
        r = self.client.get("/api/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "ok")
        self.assertIsNotNone(r.json()["local_schema_version"])

    def test_api_02_dev2_catalog(self):
        r = self.client.get("/api/domain2/catalog", headers=self.admin)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertIn("environment", r.json()["domains"])

    def test_api_03_vitals_create_and_list(self):
        r = self.client.post("/api/vitals", headers=self.admin, json=reading())
        self.assertEqual(r.status_code, 201, r.text)
        rows = self.client.get("/api/measurements", params={"mission_id": MISSION}, headers=self.admin)
        self.assertEqual(rows.status_code, 200, rows.text)
        self.assertEqual([x["event_id"] for x in rows.json()["items"]], ["read-001"])

    def test_api_04_radiation_create_and_list(self):
        d = {"dose_quantity": "effective", "original_value": 0.01,
             "original_unit": "mSv", "interval_start": T0.isoformat(),
             "interval_end": (T0 + timedelta(hours=1)).isoformat(),
             "particle_type": "unspecified"}
        self._domain_created("radiation", d)
        r = self.client.get("/api/domain2/radiation", params={"mission_id": MISSION}, headers=self.admin)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(len(r.json()["items"]), 1)

    def test_api_05_environment_create_and_list(self):
        d = {"metric_code": "ppco2", "original_value": 0.5,
             "original_unit": "kPa", "zone": "CABIN-A",
             "averaging_window_seconds": 3600,
             "calibration_revision": "sim-v1"}
        self._domain_created("environment", d)
        r = self.client.get("/api/domain2/environment", params={"mission_id": MISSION}, headers=self.admin)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(len(r.json()["items"]), 1)

    def test_api_06_sleep_create_and_list(self):
        self._domain_created("sleep", {"start_at": T0.isoformat(),
                               "end_at": (T0 + timedelta(hours=7)).isoformat()})
        r = self.client.get("/api/domain2/sleep", params={"mission_id": MISSION}, headers=self.admin)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(len(r.json()["items"]), 1)

    def test_api_07_reports_count_and_label(self):
        self._domain_created("exercise", {"exercise_type": "cycle", "duration_minutes": 30,
                                           "activity_context": "workout"})
        r = self.client.get("/api/reports/summary", params={"mission_id": MISSION}, headers=self.admin)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["domains"]["exercise"]["count"], 1)
        self.assertEqual(r.json()["domains"]["exercise"]["simulated"], 1)
        self.assertFalse(r.json()["clinical_interpretation"])

    def test_api_08_baseline_missing_is_unavailable(self):
        r = self.client.get("/api/baselines/compare", headers=self.admin,
                            params={"mission_id": MISSION, "astronaut_id": "CREW-01",
                                    "metric_code": "heart_rate", "method": "resting"})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["status"], "unavailable")

    def test_auth_01_requires_token(self):
        r = self.client.get("/api/domain2/catalog")
        self.assertEqual(r.status_code, 401, r.text)

    def test_auth_02_bad_token_rejected(self):
        r = self.client.get("/api/domain2/catalog", headers={"Authorization": "Bearer not-a-real-token"})
        self.assertEqual(r.status_code, 401, r.text)

    def test_auth_03_researcher_cannot_write(self):
        r = self._post_domain("sleep", {"start_at": T0.isoformat(), "end_at": (T0 + timedelta(hours=6)).isoformat()},
                              headers=self.researcher)
        self.assertEqual(r.status_code, 403, r.text)

    def test_auth_04_mission_scope_rejected(self):
        r = self.client.get("/api/measurements", headers=self.admin, params={"mission_id": "OTHER-MISSION"})
        self.assertEqual(r.status_code, 403, r.text)

    def test_auth_05_private_behavioral_read_denied(self):
        self._domain_created("behavioral", {"assessment_type": "demo-checkin",
                                              "visibility_classification": "PRIVATE"})
        r = self.client.get("/api/domain2/behavioral", params={"mission_id": MISSION}, headers=self.crew)
        self.assertEqual(r.status_code, 403, r.text)
        r = self.client.get("/api/reports/summary", params={"mission_id": MISSION}, headers=self.researcher)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["domains"]["behavioral"], {"access": "restricted"})

    def test_auth_06_private_behavioral_write_denied(self):
        r = self._post_domain("behavioral", {"assessment_type": "demo-checkin",
                                                    "visibility_classification": "PRIVATE"}, headers=self.crew)
        self.assertEqual(r.status_code, 403, r.text)

    def test_valid_01_invalid_vital_unit_rejected(self):
        r = self.client.post("/api/measurements", headers=self.admin,
                             json=reading(unit="Gy"))
        self.assertEqual(r.status_code, 422, r.text)

    def test_valid_02_invalid_radiation_conversion_rejected(self):
        d = {"dose_quantity": "effective", "original_value": 1,
             "original_unit": "Gy", "interval_start": T0.isoformat(),
             "interval_end": (T0 + timedelta(hours=1)).isoformat(),
             "particle_type": "unknown"}
        r = self._post_domain("radiation", d)
        self.assertEqual(r.status_code, 422, r.text)

    def test_valid_03_environment_average_window_rejected(self):
        d = {"metric_code": "ppco2", "original_value": 0.5,
             "original_unit": "kPa", "zone": "CABIN-A",
             "averaging_window_seconds": 0,
             "calibration_revision": "sim-v1"}
        self.assertEqual(self._post_domain("environment", d).status_code, 422)

    def test_valid_04_demo_staging_rejects_real_data(self):
        d = {"start_at": T0.isoformat(), "end_at": (T0 + timedelta(hours=7)).isoformat()}
        r = self._post_domain("sleep", d, source_type="REAL", is_synthetic=False)
        self.assertEqual(r.status_code, 403, r.text)

    def test_duplicate_01_same_vital_has_no_second_record(self):
        p = reading()
        self.assertEqual(self.client.post("/api/vitals", json=p, headers=self.admin).status_code, 201)
        r = self.client.post("/api/vitals", json=p, headers=self.admin)
        self.assertIn(r.status_code, (200, 201, 409), r.text)
        rows = self.client.get("/api/measurements", params={"mission_id": MISSION}, headers=self.admin).json()["items"]
        self.assertEqual(len([x for x in rows if x["event_id"] == p["event_id"]]), 1)

    def test_duplicate_02_conflicting_domain_evidence_rejected(self):
        d = {"exercise_type": "cycle", "duration_minutes": 30, "activity_context": "workout"}
        self._domain_created("exercise", d)
        changed = dict(d, duration_minutes=70)
        r = self._post_domain("exercise", changed)
        self.assertEqual(r.status_code, 409, r.text)
        rows = self.client.get("/api/domain2/exercise", params={"mission_id": MISSION}, headers=self.admin).json()["items"]
        self.assertEqual(rows[0]["data"]["duration_minutes"], 30)

    def test_sqlite_01_record_survives_restart(self):
        p = reading()
        r = self.client.post("/api/measurements", json=p, headers=self.admin)
        self.assertEqual(r.status_code, 201, r.text)
        # Close first application before reopening the identical encrypted file.
        self.client.__exit__(None, None, None)
        self.client = TestClient(self.create_app(self.settings))
        self.client.__enter__()
        r = self.client.get("/api/measurements", params={"mission_id": MISSION}, headers=self.admin)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(len(r.json()["items"]), 1)
        self.assertEqual(r.json()["items"][0]["event_id"], p["event_id"])

    def test_sqlite_02_cloud_offline_local_save(self):
        self.assertEqual(self.settings.sync_rpc_url, "")
        r = self.client.post("/api/measurements", json=reading(), headers=self.admin)
        self.assertEqual(r.status_code, 201, r.text)
        self.assertGreaterEqual(self.app.state.store.pending_count, 1)

    def test_sqlite_03_queue_status(self):
        self.client.post("/api/measurements", json=reading(), headers=self.admin)
        r = self.client.get("/api/sync/status", headers=self.admin)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertGreaterEqual(sum(r.json()["counts"].values()), 1)

    def test_sqlite_04_cloud_receipt_in_memory(self):
        from app.sync.worker import SyncWorker, MemoryReceiptTransport
        self.client.post("/api/measurements", json=reading(), headers=self.admin)
        transport = MemoryReceiptTransport()
        worker = SyncWorker(self.app.state.store, transport, batch_size=50)
        first = worker.run_once(mission_ids=[MISSION])
        self.assertGreaterEqual(first["delivered"], 1, first)
        self.assertEqual(first["failed"], 0, first)
        second = worker.run_once(mission_ids=[MISSION])
        self.assertEqual(second["delivered"], 0, second)
        self.assertEqual(second["failed"], 0, second)
        # This is a simulated receipt, not a Supabase exactly-once proof.

    def test_s01_normal_vitals_no_unapproved_alert(self):
        r = self.client.post("/api/vitals", headers=self.admin, json=reading(event_id="s01"))
        self.assertEqual(r.status_code, 201, r.text)
        self.assertEqual(r.json()["alerts"], [])

    def test_s02_workout_context_preserved(self):
        self._domain_created("exercise", {"exercise_type": "cycle", "duration_minutes": 30,
                                           "activity_context": "workout"})
        r = self.client.post("/api/vitals", headers=self.admin,
                             json=reading(value=120, event_id="s02", metadata={"activity_context": "workout"}))
        self.assertEqual(r.status_code, 201, r.text)
        self.assertEqual(r.json()["measurement"]["metadata"]["activity_context"], "workout")
        self.assertEqual(r.json()["alerts"], [])

    def test_s03_severe_symptom_without_spo2_local_incident(self):
        p = {"event_id": "s03-symptom", "mission_id": MISSION,
             "astronaut_id": "CREW-01", "symptom": "Difficulty breathing",
             "severity": "severe", "onset": T0.isoformat(),
             "body_location": "chest", "source_type": "SIMULATED",
             "is_synthetic": True, "measured_at": T0.isoformat(),
             "received_at": (T0 + timedelta(minutes=1)).isoformat(),
             "quality": "VALID", "verification": "UNVERIFIED"}
        r = self.client.post("/api/incidents/serious-symptoms", json=p, headers=self.admin)
        self.assertEqual(r.status_code, 201, r.text)
        incidents = self.client.get("/api/incidents", params={"mission_id": MISSION}, headers=self.admin)
        self.assertEqual(incidents.status_code, 200, incidents.text)
        self.assertGreaterEqual(len(incidents.json()["items"]), 1)
        vitals = self.client.get("/api/measurements", params={"mission_id": MISSION}, headers=self.admin)
        self.assertFalse(any(row.get("metric") == "spo2" for row in vitals.json()["items"]))

    @unittest.skip("S04 linked CO2/headache incident rule not implemented by the provided prototype")
    def test_s04_window_co2_headache_linked_incident(self):
        pass

    @unittest.skip("S05 D-dimer + clinician review workflow not implemented in provided prototype")
    def test_s05_ddimer_review_only(self):
        pass

    def test_s06_left_vascular_side_recorded(self):
        self._domain_created("vascular", {"exam_id": "S06-exam", "side": "LEFT",
                                                  "method": "Doppler", "review_status": "UNREVIEWED"})
        r = self.client.get("/api/domain2/vascular", params={"mission_id": MISSION}, headers=self.admin)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["items"][0]["data"]["side"], "LEFT")

    def test_s07_stale_dosimeter_preserved(self):
        d = {"dose_quantity": "effective", "original_value": 0.01,
             "original_unit": "mSv", "interval_start": T0.isoformat(),
             "interval_end": (T0 + timedelta(hours=1)).isoformat(),
             "particle_type": "unspecified"}
        r = self._post_domain("radiation", d, quality="STALE")
        self.assertEqual(r.status_code, 201, r.text)
        self.assertEqual(r.json()["event"]["quality"], "STALE")
        # Does not assert complete SPE escalation logic; that is not implemented.

    def test_s08_inflight_bone_dxa_rejected(self):
        d = {"exam_id": "S08", "anatomical_region": "lumbar_spine",
             "method": "DXA", "flight_phase": "IN_FLIGHT", "review_status": "UNREVIEWED"}
        self.assertEqual(self._post_domain("bone", d).status_code, 422)

    def test_s09_culture_sampling_method_retained(self):
        d = {"sample_id": "S09", "sample_type": "water",
             "sampling_method": "culture", "denominator_unit": "CFU/mL",
             "review_status": "UNREVIEWED"}
        self._domain_created("environmental_samples", d)
        r = self.client.get("/api/domain2/environmental_samples", params={"mission_id": MISSION}, headers=self.admin)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["items"][0]["data"]["denominator_unit"], "CFU/mL")

    def test_s10_offline_queue_and_in_memory_receipt(self):
        self.test_sqlite_04_cloud_receipt_in_memory()

    def test_s11_unapproved_operational_rule_not_triggered(self):
        r = self.client.post("/api/vitals", json=reading(event_id="s11"), headers=self.admin)
        self.assertEqual(r.status_code, 201, r.text)
        self.assertEqual(r.json()["alerts"], [])
        # This tests absence of rules only, not an expired/unapproved rule fixture.

    def test_s12_behavioral_private_denied(self):
        self.test_auth_05_private_behavioral_read_denied()


class FixtureTests(unittest.TestCase):
    def test_seed_all_required_counts(self):
        expected = {
            "vitals": 8640, "bp_pair": 240, "sleep": 120,
            "exercise": 120, "symptoms": 24, "behavioral": 20,
            "personal_dose": 120, "habitat_co2": 720,
            "oxygen_pressure": 240, "spe_context": 12,
            "biological_samples": 24, "laboratory_results": 32,
            "environmental_samples": 12, "environmental_results": 16,
            "sequencing_runs": 4, "ecg": 4, "ocular_per_eye": 16,
            "vascular": 8, "fitness": 8, "bone_regions": 8,
            "demo_catalog": 20, "inventory": 12,
            "demo_procedures": 8, "incidents_alerts": 8,
            "sync_queue_examples": 30, "delayed_receipts": 8,
            "retry_tests": 5, "duplicate_replay": 4,
        }
        with tempfile.TemporaryDirectory() as folder:
            manifest = generate(folder, 20261115)
            for name, count in expected.items():
                self.assertEqual(manifest["counts"].get(name), count, name)
            self.assertEqual(manifest["crew"], ["CREW-01", "CREW-02", "CREW-03", "CREW-04"])
            self.assertEqual(manifest["devices"], 10)
            self.assertEqual(manifest["locations"], 3)

    def test_seed_repeatability_byte_for_byte(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            one = generate(a, 20261115)
            two = generate(b, 20261115)
            self.assertEqual(one["sha256"], two["sha256"])
            self.assertEqual((Path(a) / "baseline.jsonl").read_bytes(),
                             (Path(b) / "baseline.jsonl").read_bytes())

    def test_seed_source_labels(self):
        with tempfile.TemporaryDirectory() as folder:
            generate(folder, 20261115)
            with (Path(folder) / "baseline.jsonl").open(encoding="utf-8") as f:
                for line in f:
                    r = json.loads(line)
                    self.assertEqual(r["source_type"], "SIMULATED")
                    self.assertIs(r["is_synthetic"], True)
                    self.assertNotEqual(r["verification"], "VERIFIED")

    def test_all_12_scenario_fixtures(self):
        self.assertEqual(set(SCENARIO_DESCRIPTIONS), {f"S{i:02d}" for i in range(1, 13)})
        with tempfile.TemporaryDirectory() as folder:
            for sid in SCENARIO_DESCRIPTIONS:
                manifest = generate(folder, 20261115, sid)
                self.assertEqual(manifest["record_count"], 1)
                self.assertEqual(manifest["status"], "fixture_generated_not_loaded_or_executed")
                event = json.loads((Path(folder) / f"scenario_{sid}.jsonl").read_text().strip())
                self.assertEqual(event["data"]["scenario_id"], sid)

    def test_scenario_fixtures_deterministic(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            for sid in SCENARIO_DESCRIPTIONS:
                self.assertEqual(generate(a, 20261115, sid)["sha256"],
                                 generate(b, 20261115, sid)["sha256"])

    def test_generated_data_not_inserted_into_sqlite(self):
        with tempfile.TemporaryDirectory() as folder:
            generate(folder, 20261115)
            self.assertFalse((Path(folder) / "offline.db").exists())
            self.assertFalse((Path(folder) / "astronaut_health.db").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
