"""Authorized clinical and laboratory read paths; local synthetic evidence only."""
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from app.auth.dependencies import issue_development_token
from app.core.config import Settings
from app.core.db import SessionLocal
from app.main import create_app
from app.models.dev2_models import (
    BiologicalSample, LaboratoryResult, OcularAssessment, OcularResult,
    VascularUltrasoundResult, BoneScan, BoneDensityResult, ClinicalSampleChain,
)


class ClinicalEvidenceReadTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix="rocketpulse_clinical_")
        self.addCleanup(temp.cleanup)
        settings=Settings()
        settings.environment="test"
        settings.sqlite_path=str(Path(temp.name)/"offline.db")
        settings.encryption_key=Fernet.generate_key().decode()
        settings.dev_auth_secret="clinical-read-test-key-1234567890123456"
        settings.offline_grant_secret="clinical-grant-test-secret-12345678"
        settings.sync_rpc_url=""
        settings.sync_access_token=""
        self.settings=settings
        self.client=TestClient(create_app(settings))
        self.client.__enter__()
        self.addCleanup(lambda:self.client.__exit__(None,None,None))
        self.crew="CREW-CLINICAL-"+uuid4().hex[:16]
        self.event=uuid4().hex
        now=datetime(2026,11,15,12,0,tzinfo=timezone.utc)
        with SessionLocal() as db:
            v=VascularUltrasoundResult(event_id="V-"+self.event,astronaut_id=self.crew,
                vein="INTERNAL_JUGULAR",side="LEFT",flow_pattern="STAGNANT",
                thrombus_finding="REVIEW_REQUIRED",measured_at=now,
                reviewed_by=None,is_synthetic=True)
            eye=OcularAssessment(event_id="O-"+self.event,astronaut_id=self.crew,
                test_type="OCT",assessed_at=now,measured_at=now,is_synthetic=True)
            scan=BoneScan(event_id="B-"+self.event,astronaut_id=self.crew,
                mission_phase="PREFLIGHT",scanned_at=now,measured_at=now,is_synthetic=True)
            sample=BiologicalSample(event_id="S-"+self.event,astronaut_id=self.crew,
                sample_type="BLOOD",collected_at=now,is_synthetic=True)
            db.add_all([v,eye,scan,sample]);db.flush()
            db.add_all([
              OcularResult(assessment_id=eye.id,eye="RIGHT",scan_region="RNFL_GLOBAL",
                  metric_code="RNFL_THICKNESS",value=93.0,unit="um"),
              BoneDensityResult(scan_id=scan.id,bone_region="LUMBAR_SPINE",bmd_value=1.1,unit="g/cm2"),
              LaboratoryResult(event_id="L-"+self.event,sample_id=sample.id,
                  test_code="D_DIMER",result_value=400,unit="ng/mL",assay_method="ELISA",
                  measured_at=now,is_synthetic=True),
              ClinicalSampleChain(sample_id=sample.id,custody_event="COLLECTED",
                  responsible_person="CREW-TEST",occurred_at=now),
            ])
            db.commit()

    def headers(self,role,missions=None):
        token=issue_development_token(self.settings,"qa-"+role,[role],missions or ["DEMO-01"])
        return {"Authorization":"Bearer "+token}

    def test_examination_read_requires_role_mission_and_preserves_anatomy(self):
        url=f"/api/v1/clinical/examinations/{self.crew}"
        self.assertEqual(self.client.get(url).status_code,401)
        self.assertEqual(self.client.get(url,headers=self.headers("crew")).status_code,403)
        self.assertEqual(self.client.get(url,headers=self.headers("researcher")).status_code,403)
        self.assertEqual(self.client.get(url,headers=self.headers("admin",["OTHER"])).status_code,403)
        result=self.client.get(url,headers=self.headers("flight_surgeon"))
        self.assertEqual(result.status_code,200,result.text)
        rows=result.json()
        self.assertTrue(any(r["record_table"]=="vascular_ultrasound_results" and
          "LEFT" in r["label"] for r in rows))
        self.assertTrue(any(r["record_table"]=="ocular_results" and
          "RIGHT" in r["label"] for r in rows))
        self.assertTrue(any(r["record_table"]=="bone_density_results" and
          "PREFLIGHT" in r["label"] for r in rows))
        self.assertTrue(all(r["is_synthetic"] for r in rows))

    def test_lab_read_preserves_assay_and_custody_no_diagnosis(self):
        url=f"/api/v1/clinical/laboratory/{self.crew}"
        self.assertEqual(self.client.get(url,headers=self.headers("crew")).status_code,403)
        self.assertEqual(self.client.get(url+"?mission_id=OTHER",
            headers=self.headers("admin")).status_code,403)
        result=self.client.get(url,headers=self.headers("admin"))
        self.assertEqual(result.status_code,200,result.text)
        rows=result.json()
        self.assertTrue(any(r["record_table"]=="laboratory_results"
          and "assay=ELISA" in r["details"] for r in rows))
        self.assertTrue(any(r["record_table"]=="clinical_sample_chain" for r in rows))
        self.assertFalse(any("DIAGNOSED" in r["quality"] for r in rows))


if __name__=="__main__":
    unittest.main()
