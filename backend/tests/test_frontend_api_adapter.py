"""Focused frontend integration contract checks. No external services required."""
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace

from app.integrations.frontend_api import (
    DOMAIN_TABLES, alert_dto, domain_dto, quality, source,
    verification, vital_dto,
)


class FrontendContractTests(unittest.TestCase):
    def test_vital_normalization(self):
        record = {
            "event_id": "test-event", "mission_id": "DEMO-01",
            "astronaut_id": "CREW-01", "metric": "SPO2",
            "value": 98.2, "unit": "%", "is_synthetic": True,
            "source_type": "SIMULATED", "quality": "VALID",
            "verification": "UNVERIFIED",
            "measured_at": "2026-11-15T10:00:00+00:00",
        }
        result = vital_dto(record)
        self.assertEqual(result["metric_code"], "SpO2")
        self.assertEqual(result["value"], 98.2)
        self.assertEqual(result["source_type"], "synthetic")
        self.assertEqual(result["quality"], "ok")
        self.assertTrue(result["is_synthetic"])

    def test_sqlalchemy_vital_normalization(self):
        record = SimpleNamespace(id="1", event_id="e1", astronaut_id="CREW-01",
            metric_code="HR", normalized_value=70.0, normalized_unit="bpm",
            quality_status="VALID", verification_status="UNVERIFIED",
            source_type="SIMULATED", is_synthetic=True,
            measured_at=datetime.now(timezone.utc), received_at=datetime.now(timezone.utc))
        self.assertEqual(vital_dto(record)["metric_code"], "HR")

    def test_alert_contract(self):
        result = alert_dto({"event_id": "a1", "mission_id": "DEMO-01",
            "severity": "warning", "status": "open", "message": "Human review",
            "is_synthetic": True, "rule_snapshot": {}})
        self.assertEqual(result["id"], "a1")
        self.assertEqual(result["approval_status"], "unapproved")
        self.assertTrue(result["is_synthetic"])

    def test_domains_have_explicit_mapping(self):
        self.assertEqual(len(DOMAIN_TABLES), 12)
        self.assertNotIn("BehavioralCheckin", DOMAIN_TABLES["sleep"])

    def test_provenance_is_not_silently_verified(self):
        self.assertEqual(verification("UNVERIFIED"), "unreviewed")
        self.assertEqual(quality("MISSING"), "missing")
        self.assertEqual(source("RESEARCH"), "research-only")
        self.assertEqual(domain_dto({"event_id": "e", "is_synthetic": True},
                                    "vital_signs")["quality"], "review-required")


if __name__ == "__main__":
    unittest.main()
