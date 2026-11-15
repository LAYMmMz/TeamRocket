"""Isolated local tests of the V2 cloud record kind and payload mapping.

No Supabase HTTP, no real backend databases.
"""
from __future__ import annotations
from pathlib import Path
import os
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
CODE=r'''
from pathlib import Path
from sqlalchemy import create_engine, Integer, String, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from app.models.dev2_models import Base, SymptomReport, VitalSign, EnvironmentalReading
from app.cloud_completion.outbox import activate, drain, ClinicalCloudOutbox, CLINICAL_KIND_BY_TABLE
engine=create_engine('sqlite:///'+str(Path('temp_test.db').resolve()))
Base.metadata.create_all(engine)
S=sessionmaker(bind=engine)
with S() as s:
 activate(s)
 s.add(SymptomReport(id='sym1',astronaut_id='TEST-CREW-01',mission_id='DEMO-01',severity='serious'))
 s.add(VitalSign(id='vit1',astronaut_id='TEST-CREW-01',mission_id='DEMO-01',metric_code='heart_rate',normalized_value=72,normalized_unit='bpm'))
 s.add(EnvironmentalReading(id='env1',location_id='LAB-01'))
 s.commit()
 assert s.query(ClinicalCloudOutbox).count()==3
class Store:
 def __init__(self): self.items={}
 def put(self,kind,record_id,payload,**kw):
  key=(kind,record_id)
  if key in self.items: assert self.items[key]==payload
  self.items[key]=payload
store=Store()
result=drain(store,S)
assert result['enqueued']==2 and result['pending']==1, result
assert {key[0] for key in store.items}=={'symptom','vital_sign'}
vital=next(v for (k,_),v in store.items.items() if k=='vital_sign')
assert vital['metric_code']=='heart_rate' and vital['value']==72 and vital['timestamp']
assert all(v['astronaut_id']=='TEST-CREW-01' for v in store.items.values())
assert drain(store,S)['enqueued']==0
import os
os.environ['SYNC_DEFAULT_ASTRONAUT_CODE']='TEST-CREW-01'
assert drain(store,S)['enqueued']==1
assert any(k=='environment' for k,_ in store.items)
assert drain(store,S)['enqueued']==0
print('PASS: symptom / vital_sign / environment mapping, no silent astronaut assignment, idempotent staging')
engine.dispose()
'''

def main():
    with tempfile.TemporaryDirectory(prefix='teamrocket_unified_mapping_') as d:
        root=Path(d)
        for folder in ['app','app/models','app/cloud_completion']:
            p=root/folder; p.mkdir(parents=True,exist_ok=True)
            (p/'__init__.py').write_text('')
        (root/'app/models/dev2_models.py').write_text('''from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String,Integer
class Base(DeclarativeBase): pass
class SymptomReport(Base):
 __tablename__='symptom_reports'
 id: Mapped[str]=mapped_column(String,primary_key=True)
 astronaut_id: Mapped[str]=mapped_column(String)
 mission_id: Mapped[str]=mapped_column(String)
 severity: Mapped[str]=mapped_column(String)
class VitalSign(Base):
 __tablename__='vital_signs'
 id: Mapped[str]=mapped_column(String,primary_key=True)
 astronaut_id: Mapped[str]=mapped_column(String)
 mission_id: Mapped[str]=mapped_column(String)
 metric_code: Mapped[str]=mapped_column(String)
 normalized_value: Mapped[int]=mapped_column(Integer)
 normalized_unit: Mapped[str]=mapped_column(String)
class EnvironmentalReading(Base):
 __tablename__='environmental_readings'
 id: Mapped[str]=mapped_column(String,primary_key=True)
 location_id: Mapped[str]=mapped_column(String)
''')
        import shutil
        shutil.copy2(ROOT/'app/cloud_completion/outbox.py',root/'app/cloud_completion/outbox.py')
        (root/'run.py').write_text(CODE)
        env=os.environ.copy();env['PYTHONPATH']=str(root)
        env.pop('SYNC_DEFAULT_ASTRONAUT_CODE',None)
        r=subprocess.run([sys.executable,'run.py'],cwd=root,env=env,text=True,capture_output=True)
        print(r.stdout,end='');print(r.stderr,end='',file=sys.stderr)
        if r.returncode:raise SystemExit(r.returncode)
if __name__=='__main__':main()
