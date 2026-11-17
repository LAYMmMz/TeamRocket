"""Public synthetic Supabase feed boundary tests (no real cloud credentials)."""
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

SEED = "2026-11-16T10:00:00+00:00"


def sample(metric="HR", domain="cardiorespiratory", value=72, crew="CREW-01"):
    return {
        "event_id": "RP-PUBLIC-" + crew + "-" + metric.upper() + "-00",
        "mission_id": "DEMO-01", "astronaut_code": crew,
        "domain": domain, "metric_code": metric, "value": value,
        "unit": "bpm" if metric == "HR" else "%",
        "measured_at": SEED, "quality": "VALID",
        "verification": "UNVERIFIED", "source_type": "SIMULATED",
        "is_synthetic": True, "approved_for_public": True,
    }


class StubResponse:
    def __init__(self, items, status=200):
        self.items = items
        self.status = status

    def raise_for_status(self):
        if self.status != 200:
            import httpx
            raise httpx.HTTPStatusError(
                "Supabase unavailable",
                request=httpx.Request("GET", "https://example.supabase.co"),
                response=httpx.Response(self.status),
            )

    def json(self):
        return self.items


class StubHTTP:
    items = []
    status = 200
    calls = []

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def get(self, url, *, params, headers):
        self.calls.append((url, params, headers))
        return StubResponse(self.items, self.status)


class PublicSyntheticTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="public-synthetic-")
        self.addCleanup(self.tmp.cleanup)
        settings = Settings()
        settings.environment = "test"
        settings.sqlite_path = str(Path(self.tmp.name) / "offline.db")
        settings.encryption_key = Fernet.generate_key().decode()
        settings.offline_grant_secret = "synthetic-offline-test-secret-key-32chars"
        settings.supabase_url = "https://example.supabase.co"
        settings.supabase_anon_key = "sb_publishable_synthetic-test"
        settings.sync_rpc_url = ""
        settings.sync_access_token = ""
        settings.allow_demo_rules = False
        self.client = TestClient(create_app(settings))
        self.client.__enter__()
        self.addCleanup(lambda: self.client.__exit__(None, None, None))
        self.fake = StubHTTP
        StubHTTP.items = [sample(), sample("SpO2", value=98)]
        StubHTTP.status = 200
        StubHTTP.calls = []
        mocked = patch("app.integrations.public_demo_api.httpx.Client", StubHTTP)
        mocked.start()
        self.addCleanup(mocked.stop)

    def test_command_requires_no_login_and_is_synthetic_only(self):
        r = self.client.get(
            "/api/v1/public/missions/DEMO-01/command?astronaut_id=CREW-01"
        )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["data_source"], "supabase-approved-synthetic")
        self.assertTrue(body["is_synthetic"])
        self.assertEqual(len(body["vitals"]), 2)
        self.assertEqual(len(body["crew"]), 4)
        self.assertEqual(body["alerts"], [])
        self.assertEqual(body["devices_online"], 0)
        self.assertTrue(all(v["is_synthetic"] for v in body["vitals"]))
        self.assertEqual(r.headers["x-rocketpulse-data-source"], "supabase-approved-synthetic")
        self.assertEqual(len(StubHTTP.calls), 1)
        url, params, headers = StubHTTP.calls[0]
        self.assertEqual(url, "https://example.supabase.co/rest/v1/rocketpulse_public_demo_samples")
        self.assertEqual(headers, {"apikey": "sb_publishable_synthetic-test", "Accept": "application/json"})
        self.assertEqual(params["mission_id"], "eq.DEMO-01")
        self.assertEqual(params["approved_for_public"], "eq.true")
        self.assertEqual(params["is_synthetic"], "eq.true")
        self.assertEqual(params["source_type"], "eq.SIMULATED")
        self.assertNotIn("Authorization", headers)

    def test_trends_and_domain_share_only_approved_synthetic_metrics(self):
        trend = self.client.get("/api/v1/public/measurements/trends?astronaut_id=CREW-01")
        self.assertEqual(trend.status_code, 200, trend.text)
        self.assertEqual(trend.json()[0]["HR"], 72)
        domain = self.client.get(
            "/api/v1/public/reports/domains/cardiorespiratory?astronaut_id=CREW-01"
        )
        self.assertEqual(domain.status_code, 200, domain.text)
        self.assertTrue(all(item["is_synthetic"] for item in domain.json()))
        self.assertTrue(all(item["record_table"] == "rocketpulse_public_demo_samples" for item in domain.json()))
        self.assertTrue(all(call[1]["domain"] == "eq.cardiorespiratory"
                            for call in StubHTTP.calls[-2:]))

    def test_fail_closed_when_feed_missing_or_upstream_unavailable(self):
        StubHTTP.items = []
        r = self.client.get(
            "/api/v1/public/missions/DEMO-01/command?astronaut_id=CREW-01"
        )
        self.assertEqual(r.status_code, 503)
        StubHTTP.status = 401
        r = self.client.get(
            "/api/v1/public/missions/DEMO-01/command?astronaut_id=CREW-01"
        )
        self.assertEqual(r.status_code, 503)
        self.assertNotIn("sb_publishable_", r.text)

    def test_reject_private_or_unapproved_rows(self):
        for update in [
            {"approved_for_public": False},
            {"source_type": "REAL", "is_synthetic": False},
            {"mission_id": "PRIVATE"},
            {"astronaut_code": "CREW-02"},
            {"metric_code": "HEALTH_NOTES"},
        ]:
            StubHTTP.items = [dict(sample(), **update)]
            r = self.client.get(
                "/api/v1/public/missions/DEMO-01/command?astronaut_id=CREW-01"
            )
            self.assertEqual(r.status_code, 503, update)

    def test_undefined_indices_are_not_presented_as_clinical_readings(self):
        for metric, domain in [("IMMUNE_INDEX", "immune"), ("BONE_INDEX", "bone"),
                               ("VASCULAR_INDEX", "vascular"), ("OCT_INDEX", "vision"),
                               ("CULTURE_INDEX", "microbiology")]:
            StubHTTP.items = [sample(metric, domain, 1)]
            response = self.client.get(
                f"/api/v1/public/reports/domains/{domain}?astronaut_id=CREW-01")
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json(), [])

    def test_empty_domain_is_unavailable_not_fabricated(self):
        StubHTTP.items = []
        response = self.client.get("/api/v1/public/reports/domains/vision?astronaut_id=CREW-01")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_metric_domain_and_unit_must_agree(self):
        for update in [{"unit": "mSv"}, {"domain": "immune"}, {"value": "NaN"}]:
            StubHTTP.items = [dict(sample(), **update)]
            response = self.client.get("/api/v1/public/missions/DEMO-01/command?astronaut_id=CREW-01")
            self.assertEqual(response.status_code, 503, response.text)
        StubHTTP.items = [sample()]
        response = self.client.get("/api/v1/public/reports/domains/sleep?astronaut_id=CREW-01")
        self.assertEqual(response.status_code, 503)

    def test_other_missions_and_invalid_crews_are_denied(self):
        self.assertEqual(self.client.get(
            "/api/v1/public/missions/PRIVATE/command?astronaut_id=CREW-01"
        ).status_code, 404)
        self.assertEqual(self.client.get(
            "/api/v1/public/missions/DEMO-01/command?astronaut_id=REAL-01"
        ).status_code, 422)
        self.assertEqual(self.client.get(
            "/api/v1/public/reports/domains/sleep_notes?astronaut_id=CREW-01"
        ).status_code, 404)

    def test_schema_catalog_reads_only_approved_metadata_and_validates_completeness(self):
        from app.integrations.public_demo_api import CANONICAL_SCHEMA_NAMES
        entries = [{
            "table_name": name,
            "table_present": True,
            "starter_fields_verified": True,
            "starter_field_count": 4,
            "missing_starter_fields": [],
            "published_synthetic_rows": 8880 if name == "vital_signs" else None,
            "inspected_at": "2026-11-17T08:46:10+00:00",
            "approved_for_public": True,
            "source_label": "verified_supabase_metadata_snapshot",
        } for name in sorted(CANONICAL_SCHEMA_NAMES)]
        StubHTTP.items = entries
        res = self.client.get("/api/v1/public/schema/catalog")
        self.assertEqual(res.status_code, 200, res.text)
        obj = res.json()
        self.assertEqual(obj["source"], "supabase-approved-schema-snapshot")
        self.assertEqual(obj["expected_tables"], 57)
        self.assertEqual(obj["verified_tables"], 57)
        self.assertEqual(len(obj["tables"]), 57)
        self.assertEqual(next(x for x in obj["tables"] if x["name"] == "vital_signs")["published_synthetic_rows"], 8880)
        url, params, headers = StubHTTP.calls[-1]
        self.assertTrue(url.endswith("/rest/v1/rocketpulse_public_schema_catalog"))
        self.assertEqual(params["approved_for_public"], "eq.true")
        self.assertNotIn("Authorization", headers)
        self.assertNotIn("service_role", str(headers))
        StubHTTP.items = entries[:-1]
        self.assertEqual(self.client.get("/api/v1/public/schema/catalog").status_code, 503)
        StubHTTP.items = entries[:-1] + [dict(entries[-1], table_name="secret_notes")]
        self.assertEqual(self.client.get("/api/v1/public/schema/catalog").status_code, 503)
        StubHTTP.items = entries[:-1] + [dict(entries[-1], approved_for_public=False)]
        self.assertEqual(self.client.get("/api/v1/public/schema/catalog").status_code, 503)
        StubHTTP.items = entries[:-1] + [dict(entries[-1], published_synthetic_rows=-5)]
        self.assertEqual(self.client.get("/api/v1/public/schema/catalog").status_code, 503)

    def test_private_api_and_public_write_stay_protected(self):
        self.assertEqual(self.client.get(
            "/api/v1/missions/DEMO-01/command?astronaut_id=CREW-01"
        ).status_code, 401)
        self.assertEqual(self.client.post(
            "/api/v1/measurements", json={}
        ).status_code, 401)
        self.assertEqual(self.client.post(
            "/api/v1/public/measurements/trends"
        ).status_code, 405)


if __name__ == "__main__":
    unittest.main()
