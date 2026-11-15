"""Check patcher against minimally representative Dev1 + friend-merge anchors."""
from pathlib import Path
import tempfile,subprocess,sys,shutil
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='teamrocket_installer_') as d:
 b=Path(d)/'backend'
 for path in ['app/offline/store.py','app/core/dev1_bridge.py','app/models/dev2_models.py','app/dev2_friend_attach.py']:
  p=b/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('')
 (b/'app/core/db.py').write_text('''from app.models.dev2_models import Base

def get_db():
    db = SessionLocal()
    db.info["store"] = None
    try:
        yield db
        db.commit()
    finally:
        db.close()
''')
 (b/'app/main.py').write_text('''def make():
        app.state.store = Store(settings)
''')
 (b/'app/sync').mkdir()
 (b/'app/sync/worker.py').write_text('''import hashlib

def send(client, event, headers):
            response = client.post(
                self.url, json={"p_event": event}, headers=headers
            )

def check(receipt):
                if not isinstance(receipt, dict) or (
                    receipt.get("event_id") is None
                ):
                    raise ValueError('bad')
''')
 shutil.copy2(ROOT/'install_cloud_completion.py',b/'install_cloud_completion.py')
 # First the actual run
 r=subprocess.run([sys.executable,'install_cloud_completion.py','--source',str(ROOT)],cwd=b,text=True,capture_output=True)
 print('installer return:',r.returncode)
 print(r.stdout,r.stderr)
 assert r.returncode==0
 assert (b/'app/cloud_completion/outbox.py').is_file()
 for path in ['app/core/db.py','app/main.py','app/sync/worker.py']:
  source=(b/path).read_text();assert 'TEAMROCKET_CLINICAL_OUTBOX_V1' in source
  compile(source,path,'exec')
 assert list(b.glob('_cloud_completion_source_backup_*'))
 # Idempotency/refusal (no accidental double installation)
 rr=subprocess.run([sys.executable,'install_cloud_completion.py','--source',str(ROOT)],cwd=b,text=True,capture_output=True)
 assert rr.returncode!=0
 print('PASS: installation, source backups, syntax and double-install refusal')
