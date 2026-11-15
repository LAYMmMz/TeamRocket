from pathlib import Path
import sys,unittest
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.domain2.contracts import DomainEvent,validate_domain
from scripts.seed_demo import generate,baseline,SCENARIO_DESCRIPTIONS
import tempfile

def event(data,**kw):
    v={'event_id':'demo-e1','mission_id':'DEMO-01','astronaut_id':'CREW-01',
      'source_type':'SIMULATED','is_synthetic':True,'measured_at':'2026-11-01T00:00:00Z',
      'received_at':'2026-11-01T00:01:00Z','quality':'VALID','verification':'UNVERIFIED',
      'source_reference':'demo','source_revision':'v1','data':data}
    v.update(kw)
    return DomainEvent.model_validate(v)
class ContractTests(unittest.TestCase):
    def test_synthetic_consistency(self):
        with self.assertRaises(ValueError): event({'foo':1},source_type='REAL')
    def test_radiation_no_unjustified_units(self):
        d={'dose_quantity':'effective','original_value':3,'original_unit':'Gy',
           'interval_start':'2026-11-01T00:00:00Z','interval_end':'2026-11-01T01:00:00Z','particle_type':'unspecified'}
        with self.assertRaisesRegex(ValueError,'compatible dose'):validate_domain('radiation',event(d))
    def test_eye_and_bone(self):
        with self.assertRaisesRegex(ValueError,'Eye'):validate_domain('ocular',event({'exam_id':'x','eye':'BOTH','region':'macula','method':'OCT','review_status':'UNREVIEWED'}))
        with self.assertRaisesRegex(ValueError,'in-flight'):validate_domain('bone',event({'exam_id':'x','anatomical_region':'spine','method':'DXA','flight_phase':'IN_FLIGHT','review_status':'UNREVIEWED'}))
    def test_private_behavior(self):
        with self.assertRaisesRegex(ValueError,'private'):validate_domain('behavioral',event({'assessment_type':'test','visibility_classification':'PUBLIC'}))
    def test_seed_reproducible_and_counts(self):
        with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b:
            m1=generate(a,20261115);m2=generate(b,20261115)
            self.assertEqual(m1['sha256'],m2['sha256'])
            self.assertEqual(m1['counts']['vitals'],8640)
            self.assertEqual(m1['counts']['bp_pair'],240)
            self.assertEqual(m1['counts']['habitat_co2'],720)
    def test_scenarios_stable(self):
        self.assertEqual(len(SCENARIO_DESCRIPTIONS),12)
        with tempfile.TemporaryDirectory() as t:
            m1=generate(t,20261115,'S03');m2=generate(t,20261115,'S03')
            self.assertEqual(m1['sha256'],m2['sha256'])
if __name__=='__main__':unittest.main()
