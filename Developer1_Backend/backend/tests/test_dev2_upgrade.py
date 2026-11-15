"""Run with: python -m unittest discover -s tests -v
This file tests safety/descriptive logic; end-to-end scenarios need separate integration QA.
"""
import unittest
from datetime import datetime, timedelta, timezone
from app.domain2.clinical_logic import (
    moment, active_examination, matched_comparisons, radiation_summary,
    environmental_window, review_plan,
)
from app.domain2.contracts import DomainEvent, validate_domain

T=datetime(2026,11,15,tzinfo=timezone.utc)

def event(eid, domain, d, *, verified=True, at=T, crew='CREW-01'):
    return {'event_id':eid,'astronaut_id':crew,'mission_id':'DEMO-01',
            'measured_at':at.isoformat(),'received_at':(at+timedelta(minutes=1)).isoformat(),
            'source_type':'SIMULATED','is_synthetic':True,'quality':'VALID',
            'verification':'VERIFIED' if verified else 'UNVERIFIED','data':d,'domain':domain}

class Dev2ClinicalSafetyTests(unittest.TestCase):
    def test_01_exams_planned_due_overdue(self):
        r=event('a','exams',{'status':'PLANNED','scheduled_at':T.isoformat()})
        self.assertEqual(active_examination(r,T),'DUE')
        self.assertEqual(active_examination(r,T+timedelta(minutes=1)),'OVERDUE')
        self.assertEqual(active_examination(r,T-timedelta(minutes=1)),'PLANNED')

    def test_02_exams_cancelled_never_fabricates_result(self):
        r=event('a','exams',{'status':'CANCELLED','scheduled_at':T.isoformat()})
        self.assertEqual(active_examination(r,T+timedelta(days=1)),'CANCELLED')

    def test_03_radiation_compatible_intervals(self):
        one=event('1','radiation',{'dose_quantity':'effective','original_value':0.5,'original_unit':'mSv',
                                  'interval_start':T.isoformat(),'interval_end':(T+timedelta(hours=1)).isoformat(),'particle_type':'proton'})
        two=event('2','radiation',{**one['data'],'original_value':0.75,'interval_start':(T+timedelta(hours=1)).isoformat(),
                                   'interval_end':(T+timedelta(hours=2)).isoformat()})
        r=radiation_summary([one,two]);self.assertEqual(r['totals'][0]['total'],1.25)
        self.assertEqual(r['totals'][0]['count'],2)

    def test_04_radiation_excludes_overlap(self):
        d={'dose_quantity':'equivalent','original_value':1.0,'original_unit':'mSv',
           'interval_start':T.isoformat(),'interval_end':(T+timedelta(hours=2)).isoformat(),'particle_type':'proton'}
        a=event('1','radiation',d);b=event('2','radiation',{**d,'interval_start':(T+timedelta(hours=1)).isoformat()})
        r=radiation_summary([a,b]);self.assertEqual(r['totals'][0]['total'],1.0)
        self.assertEqual(r['excluded'][0]['reason'],'overlapping_interval')

    def test_05_radiation_never_adds_dose_rate(self):
        d={'dose_quantity':'rate','original_value':1.0,'original_unit':'mSv/h',
           'interval_start':T.isoformat(),'interval_end':(T+timedelta(hours=1)).isoformat(),'particle_type':'proton'}
        r=radiation_summary([event('1','radiation',d)])
        self.assertEqual(r['totals'],[])
        self.assertEqual(r['excluded'][0]['reason'],'incompatible_dose_quantity_or_unit')

    def test_06_unverified_radiation_never_summed(self):
        d={'dose_quantity':'effective','original_value':1,'original_unit':'mSv',
           'interval_start':T.isoformat(),'interval_end':(T+timedelta(hours=1)).isoformat(),'particle_type':'proton'}
        self.assertEqual(radiation_summary([event('x','radiation',d,verified=False)])['totals'],[])

    def test_07_environment_uses_average_window_and_verified_only(self):
        d={'metric_code':'ppco2','original_value':0.5,'original_unit':'kPa','zone':'CABIN-A',
           'averaging_window_seconds':3600,'calibration_revision':'demo-1'}
        a=event('a','environment',d);b=event('b','environment',{**d,'averaging_window_seconds':10})
        c=event('c','environment',d,verified=False)
        result=environmental_window([a,b,c],'ppco2','CABIN-A')
        self.assertEqual(len(result['windows']),1)
        self.assertFalse(result['operational_alarm'])

    def test_08_ocular_does_not_compare_other_eyes(self):
        d={'eye':'LEFT','region':'macula','method':'OCT','original_unit':'um','original_value':200}
        a=event('a','ocular',d);b=event('b','ocular',{**d,'eye':'RIGHT','original_value':300})
        self.assertEqual(matched_comparisons([a,b],group_fields=('eye','region','method')),[])

    def test_09_matched_eyes_methods_are_descriptive(self):
        d={'eye':'LEFT','region':'macula','method':'OCT','original_unit':'um','original_value':200}
        a=event('a','ocular',d);b=event('b','ocular',{**d,'original_value':210},at=T+timedelta(days=1))
        r=matched_comparisons([a,b],group_fields=('eye','region','method'))
        self.assertEqual(r[0]['difference'],10.0)
        self.assertFalse(r[0]['clinical_interpretation'])

    def test_10_bone_no_cross_region_comparison(self):
        d={'anatomical_region':'lumbar_spine','method':'DXA','original_unit':'g/cm2','original_value':1.1}
        a=event('a','bone',d);b=event('b','bone',{**d,'anatomical_region':'femoral_neck','original_value':0.9})
        self.assertEqual(matched_comparisons([a,b],group_fields=('anatomical_region','method')),[])

    def test_11_water_culture_review_requires_human(self):
        r=review_plan('environmental_samples',event('x','environmental_samples',{'flagged':True}))
        self.assertIn('request_repeat_sampling',r['suggested_manual_actions'])
        self.assertFalse(r['medical_diagnosis'])

    def test_12_gravity_does_not_clear_eva(self):
        r=review_plan('gravity',event('x','gravity',{'transition_type':'microgravity'}))
        self.assertFalse(r['eva_clearance_granted'])
        self.assertIn('human_eva_clearance_review',r['suggested_manual_actions'])

    def test_13_sequence_not_diagnosis(self):
        r=review_plan('sequencing',event('x','sequencing',{'qc_status':'FAIL'}))
        self.assertIn('manual_sequence_qc_and_reviewer_signoff',r['suggested_manual_actions'])
        self.assertFalse(r['medical_diagnosis'])

    def test_14_source_consistency_blocks_mislabeled_data(self):
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            DomainEvent(event_id='1',mission_id='DEMO-01',source_type='REAL',is_synthetic=True,
                        measured_at=T,received_at=T,quality='VALID',verification='UNVERIFIED',
                        source_reference='fixture',source_revision='1',data={'x':1})

    def test_15_invalid_environment_averaging_window_blocked(self):
        e=DomainEvent(event_id='1',mission_id='DEMO-01',source_type='SIMULATED',is_synthetic=True,
                        measured_at=T,received_at=T,quality='VALID',verification='UNVERIFIED',
                        source_reference='fixture',source_revision='1',data={
                            'metric_code':'ppco2','original_value':0.5,'original_unit':'kPa',
                            'zone':'CABIN-A','averaging_window_seconds':0,'calibration_revision':'demo-1'})
        with self.assertRaises(ValueError): validate_domain('environment',e)

    def test_16_no_clinical_diagnosis_from_ddimer(self):
        r=review_plan('lab_results',event('x','lab_results',{'assay_code':'D-dimer'}))
        self.assertFalse(r['medical_diagnosis'])
        self.assertIn('clinician_review',r['suggested_manual_actions'])

    def test_17_timezone_naive_rejected(self):
        with self.assertRaises(ValueError): moment('2026-11-15T12:00:00')

if __name__=='__main__':unittest.main()
