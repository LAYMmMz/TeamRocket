"""Isolated behavioral unit test, no project DB and no cloud credentials."""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap

ROOT=Path(__file__).resolve().parents[1]

SCRIPT = '''
import sys
from datetime import datetime
from sqlalchemy import create_engine, String, Integer, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, sessionmaker
from pathlib import Path
from app.cloud_completion.outbox import ClinicalCloudOutbox,activate,drain
from app.models.dev2_models import Base, VitalSign
engine=create_engine('sqlite:///'+str(Path('clinical_test.db').resolve()))
Base.metadata.create_all(engine)
SessionLocal=sessionmaker(engine)
with SessionLocal() as session:
 activate(session)
 session.add(VitalSign(id='TEST-1', astronaut_id='ASTRO-1', metric_code='HR', value=68))
 session.commit()
 assert session.query(ClinicalCloudOutbox).count()==1
 row=session.scalars(select(ClinicalCloudOutbox)).one()
 assert row.status=='pending'
class Store:
 def __init__(self):self.data={}
 def put(self,kind,record_id,payload,**opts):
  key=(kind,record_id)
  if key in self.data:assert self.data[key]==payload
  self.data[key]=payload
store=Store()
assert drain(store,SessionLocal)['enqueued']==1
assert drain(store,SessionLocal)['enqueued']==0
assert len(store.data)==1
with SessionLocal() as session:
 r=session.scalars(select(ClinicalCloudOutbox)).one()
 assert r.status=='enqueued'
print('PASS: transactional clinical outbox + idempotent staging')
engine.dispose()
'''

def main():
 with tempfile.TemporaryDirectory(prefix='teamrocket_outbox_isolated_') as root:
  root=Path(root)
  app=root/'app'
  (app/'models').mkdir(parents=True)
  (app/'cloud_completion').mkdir(parents=True)
  for dir in (app,app/'models',app/'cloud_completion'):
   (dir/'__init__.py').write_text('',encoding='utf-8')
  (app/'models'/'dev2_models.py').write_text('''from sqlalchemy import String, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
class Base(DeclarativeBase): pass
class VitalSign(Base):
 __tablename__='vital_signs'
 id: Mapped[str] = mapped_column(String, primary_key=True)
 astronaut_id: Mapped[str] = mapped_column(String)
 metric_code: Mapped[str] = mapped_column(String)
 value: Mapped[int] = mapped_column(Integer)
''',encoding='utf-8')
  import shutil
  shutil.copy2(ROOT/'app/cloud_completion/outbox.py',app/'cloud_completion/outbox.py')
  (root/'run.py').write_text(SCRIPT,encoding='utf-8')
  env=os.environ.copy()
  env['PYTHONPATH']=str(root)
  res=subprocess.run([sys.executable,'run.py'], cwd=root, env=env,capture_output=True,text=True)
  print(res.stdout,res.stderr)
  if res.returncode:raise SystemExit(res.returncode)

if __name__=='__main__':main()
