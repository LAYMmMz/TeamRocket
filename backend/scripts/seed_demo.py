"""Deterministic synthetic fixtures for TeamRocket T07/T29, NOT production seed.

Usage: python scripts/seed_demo.py --seed 20261115 --profile baseline
       python scripts/seed_demo.py --seed 20261115 --scenario S03
       python scripts/seed_demo.py --reset
Outputs synthetic JSONL + checksum manifest in ./demo_output; does not alter any DB.
"""
from __future__ import annotations
import argparse,hashlib,json,math,os,random,uuid
from collections import Counter
from datetime import datetime,timedelta,timezone
from pathlib import Path

BASE = datetime(2026, 11, 1, tzinfo=timezone.utc)
MISSION='DEMO-01'
CREW=[f'CREW-{i:02d}' for i in range(1,5)]
ROLES=['admin','flight_surgeon','crew','mission_control','researcher']
SCENARIO_DESCRIPTIONS={
'S01':'Normal vitals/environment; no inappropriate alerts',
'S02':'Exercise context distinguishes activity-associated HR',
'S03':'Serious breathing symptom with missing SpO2; requires local incident',
'S04':'Time-window CO2 and headache; linked evidence for review',
'S05':'Unreviewed D-dimer; review only, no diagnosis',
'S06':'Left-side ultrasound finding; reviewed per-side record',
'S07':'SPE context plus stale dosimeter; mark reading stale',
'S08':'OCT due; absent in-flight DXA cannot be fabricated',
'S09':'Water culture flag; sampling-method-aware resampling review',
'S10':'Network disconnect/reconnect; replay receipt test required',
'S11':'Expired procedure and unapproved rule; operational use blocked',
'S12':'Unauthorized behavioral check-in access; deny and audit',
}

def stable_id(seed,kind,index):
    return str(uuid.uuid5(uuid.NAMESPACE_URL,f'TeamRocket/{seed}/{kind}/{index}'))

def record(seed,kind,index,crew,when,data,quality='VALID',verification='UNVERIFIED'):
    return {
        'event_id':stable_id(seed,kind,index),'kind':kind,'mission_id':MISSION,
        'astronaut_id':crew,'source_type':'SIMULATED','is_synthetic':True,
        'measured_at':when.isoformat(),'received_at':(when+timedelta(seconds=10)).isoformat(),
        'quality':quality,'verification':verification,'source_reference':'TeamRocket synthetic test fixture',
        'source_revision':'seed-v1','data':data,
    }

def baseline(seed):
    """Produce all records with stable IDs and a fixed clock, never time.time()."""
    rng=random.Random(seed)
    # Exactly 8,640 HR/SpO2/RR records plus 240 combined BP observations.
    for ci,crew in enumerate(CREW):
        for day in range(30):
            for hour in range(24):
                t=BASE+timedelta(days=day,hours=hour)
                for metric,unit,base in [('heart_rate','bpm',72),('spo2','%',97),('respiratory_rate','breaths/min',15)]:
                    val=round(base+math.sin((day*24+hour)/7+ci)*({'heart_rate':7,'spo2':0.6,'respiratory_rate':2}[metric]),2)
                    i=f'{crew}/{day:02d}/{hour:02d}/{metric}'
                    yield record(seed,'vitals',i,crew,t,{'metric_code':metric,'original_value':val,'original_unit':unit,'activity_context':'unclassified_demo'})
        for day in range(30):
            for twice in range(2):
                t=BASE+timedelta(days=day,hours=8+12*twice)
                i=f'{crew}/{day:02d}/{twice}/bp'
                yield record(seed,'bp_pair',i,crew,t,{'systolic':115+rng.randrange(-5,6),'diastolic':75+rng.randrange(-4,5),'unit':'mmHg'})
    counts={
        'sleep':120,'exercise':120,'symptoms':24,'behavioral':20,
        'personal_dose':120,'habitat_co2':720,'oxygen_pressure':240,'spe_context':12,
        'biological_samples':24,'laboratory_results':32,'environmental_samples':12,
        'environmental_results':16,'sequencing_runs':4,'ecg':4,'ocular_per_eye':16,
        'vascular':8,'fitness':8,'bone_regions':8,'demo_catalog':20,
        'inventory':12,'demo_procedures':8,'incidents_alerts':8,
        'sync_queue_examples':30,'delayed_receipts':8,'retry_tests':5,'duplicate_replay':4,
    }
    for kind,n in counts.items():
        for i in range(n):
            crew=CREW[i%len(CREW)]
            t=BASE+timedelta(hours=i*3)
            data={'fixture_index':i,'domain':kind,'clinical_interpretation':False,'review_status':'DEMO_ONLY'}
            if kind=='behavioral':data['visibility_classification']='PRIVATE'
            if kind=='sleep':data.update(start_at=t.isoformat(),end_at=(t+timedelta(hours=7)).isoformat())
            if kind=='exercise':data.update(exercise_type='cycle_ergometer',duration_minutes=30,activity_context='simulated_workout')
            if kind=='personal_dose':data.update(dose_quantity='effective',original_value=0.01,original_unit='mSv',interval_start=t.isoformat(),interval_end=(t+timedelta(hours=1)).isoformat(),particle_type='unspecified')
            if kind=='habitat_co2':data.update(metric_code='ppco2',original_value=0.50,original_unit='kPa',averaging_window_seconds=3600,zone='CABIN-A',calibration_revision='sim-v1')
            if kind=='ocular_per_eye':data.update(eye='LEFT' if i%2==0 else 'RIGHT',region='macula',method='OCT',review_status='UNREVIEWED')
            if kind=='bone_regions':data.update(anatomical_region='lumbar_spine',flight_phase='PRE' if i%2==0 else 'POST',method='DXA')
            yield record(seed,kind,i,crew,t,data)

def scenario(seed,name):
    if name not in SCENARIO_DESCRIPTIONS:raise ValueError('Unknown scenario')
    return record(seed,'scenario',name,CREW[0],BASE+timedelta(days=30),{
        'scenario_id':name,'description':SCENARIO_DESCRIPTIONS[name],
        'expected_behavior':'requires domain/alert/authorization acceptance test',
        'auto_clinical_decision':False,'simulated':True,
    })

def generate(output,seed,selected=None):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    records=list([scenario(seed,selected)] if selected else baseline(seed))
    datafile=output/('scenario_'+selected+'.jsonl' if selected else 'baseline.jsonl')
    # Stable byte-for-byte output for an identical seed and profile.
    payload=''.join(json.dumps(r,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n' for r in records).encode('utf-8')
    datafile.write_bytes(payload)
    counts=Counter(x['kind'] for x in records)
    manifest={'seed':seed,'mission':MISSION,'crew':CREW,'roles':ROLES,'devices':10,'locations':3,
      'profile':selected or 'baseline','record_count':len(records),'counts':dict(sorted(counts.items())),
      'sha256':hashlib.sha256(payload).hexdigest(),'filename':datafile.name,'clinical_interpretation':False,
      'status':'fixture_generated_not_loaded_or_executed'}
    (output/('manifest_'+selected+'.json' if selected else 'manifest_baseline.json')).write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    return manifest

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed',type=int,default=20261115)
    parser.add_argument('--profile',choices=['baseline'],default='baseline')
    parser.add_argument('--scenario',choices=sorted(SCENARIO_DESCRIPTIONS))
    parser.add_argument('--output',default='demo_output')
    parser.add_argument('--reset',action='store_true')
    args=parser.parse_args()
    output=Path(args.output).resolve()
    if args.reset:
        if os.getenv('APP_ENV','development') not in ('development','test'):
            raise SystemExit('Reset blocked outside development/test')
        # Refuse to delete arbitrary files or folders. Only delete our generated fixtures.
        if output.exists():
            for p in output.iterdir():
                if p.is_file() and (p.name=='baseline.jsonl' or p.name.startswith('scenario_') and p.name.endswith('.jsonl') or p.name.startswith('manifest_') and p.name.endswith('.json')):
                    p.unlink()
        print('Removed only generated synthetic fixture files');return
    m=generate(output,args.seed,args.scenario)
    print(json.dumps(m,indent=2))

if __name__=='__main__':main()
