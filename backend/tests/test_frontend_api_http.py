"""Protected, in-process, synthetic-only frontend integration smoke tests.

No Supabase account or user's database is accessed.
"""
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from app.auth.dependencies import issue_development_token
from app.core.config import Settings
from app.main import create_app


class FrontendHTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="rocketpulse_http_")
        self.addCleanup(self.tmp.cleanup)
        settings = Settings()
        settings.environment = "test"
        settings.sqlite_path = str(Path(self.tmp.name) / "offline.db")
        settings.encryption_key = Fernet.generate_key().decode()
        settings.dev_auth_secret = "rocketpulse-test-jwt-signing-secret-123456"
        settings.offline_grant_secret = "rocketpulse-test-grant-secret-12345678"
        settings.sync_rpc_url = ""
        settings.sync_access_token = ""
        settings.allow_demo_rules = False
        settings.cors_origins = ["https://teamrocket.example"]
        self.settings = settings
        self.client = TestClient(create_app(settings))
        self.client.__enter__()
        self.addCleanup(lambda: self.client.__exit__(None, None, None))
        self.admin = self.headers("admin")
        self.crew = self.headers("crew")
        self.researcher = self.headers("researcher")

    def headers(self, role, missions=None):
        token = issue_development_token(
            self.settings, "qa-" + role, [role],
            missions or ["DEMO-01"], ttl_minutes=60,
        )
        return {"Authorization": "Bearer " + token}

    def test_auth_and_mission_scope(self):
        url = "/api/v1/missions/DEMO-01/command?astronaut_id=CREW-01"
        self.assertEqual(self.client.get(url).status_code, 401)
        self.assertEqual(self.client.get(url, headers=self.admin).status_code, 200)
        self.assertEqual(self.client.get(url, headers=self.headers("admin", ["OTHER"])).status_code, 403)
        self.assertEqual(self.client.get(url, headers=self.researcher).status_code, 403)

    def test_cors_preflight_allows_idempotency_header_only_for_explicit_origin(self):
        headers = {
            "Origin": "https://teamrocket.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type,idempotency-key",
        }
        resp = self.client.options("/api/v1/symptoms", headers=headers)
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(resp.headers.get("access-control-allow-origin"), "https://teamrocket.example")
        self.assertNotEqual(
            self.client.options("/api/v1/symptoms", headers={
                **headers, "Origin": "https://unauthorized.example",
            }).status_code, 200
        )

    def test_measurement_to_frontend_command_and_trends(self):
        sample = {
            "event_id": "test-vital-one", "mission_id": "DEMO-01",
            "astronaut_id": "CREW-01", "metric": "heart_rate",
            "value": 72, "unit": "bpm",
            "source_type": "SIMULATED", "is_synthetic": True,
            "measured_at": datetime.now(timezone.utc).isoformat(),
            "quality": "VALID", "verification": "UNVERIFIED",
            "source_reference": "http-contract-test",
            "source_revision": "v1",
        }
        ingest = self.client.post("/api/measurements", json=sample, headers=self.admin)
        self.assertEqual(ingest.status_code, 201, ingest.text)
        command = self.client.get(
            "/api/v1/missions/DEMO-01/command?astronaut_id=CREW-01",
            headers=self.crew,
        )
        self.assertEqual(command.status_code, 200, command.text)
        self.assertEqual(command.json()["vitals"][0]["metric_code"], "HR")
        self.assertTrue(command.json()["vitals"][0]["is_synthetic"])
        trend = self.client.get(
            "/api/v1/measurements/trends?astronaut_id=CREW-01",
            headers=self.crew,
        )
        self.assertEqual(trend.status_code, 200, trend.text)
        self.assertTrue(any(point["HR"] == 72 for point in trend.json()))

    def test_alert_acknowledgement_requires_clinician(self):
        self.assertEqual(self.client.post(
            "/api/v1/alerts/missing/acknowledgments",
            json={"action": "acknowledge"}, headers=self.crew,
        ).status_code, 403)
        self.assertEqual(self.client.post(
            "/api/v1/alerts/missing/acknowledgments",
            json={"action": "acknowledge"}, headers=self.admin,
        ).status_code, 404)

    def test_symptom_write_provenance_and_no_unverified_cloud_receipt(self):
        body = {
            "event_id": "test-symptom-01", "mission_id": "DEMO-01",
            "astronaut_id": "CREW-01", "symptom_code": "headache",
            "severity": "mild", "notes": "Synthetic integration test",
            "is_synthetic": True,
        }
        r = self.client.post("/api/v1/symptoms", json=body, headers=self.crew)
        self.assertEqual(r.status_code, 201, r.text)
        self.assertTrue(r.json()["persisted_locally"])
        self.assertFalse(r.json()["cloud_receipt_confirmed"])
        record = self.client.app.state.store.get("symptom_report", body["event_id"])
        self.assertEqual(record["source_type"], "SIMULATED")

    def test_manual_cloud_sync_requires_privileged_user_and_configuration(self):
        endpoint = "/api/v1/sync/run?mission_id=DEMO-01"
        # No JWT is rejected; crew must not trigger cloud writes.
        self.assertEqual(self.client.post(endpoint).status_code, 401)
        self.assertEqual(
            self.client.post(endpoint, headers=self.crew).status_code, 403
        )
        # A scoped admin still cannot sync when the remote RPC is disabled.
        result = self.client.post(endpoint, headers=self.admin)
        self.assertEqual(result.status_code, 503, result.text)

    def test_sync_status_is_privileged(self):
        self.assertEqual(self.client.get("/api/v1/sync/status", headers=self.crew).status_code, 403)
        r = self.client.get("/api/v1/sync/status", headers=self.admin)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["last_receipt_at"], None)


if __name__ == "__main__":
    unittest.main()
