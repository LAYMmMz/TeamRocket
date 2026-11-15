"""Run after installing source patch. Static checks only; do not modify real databases."""
from pathlib import Path
import ast
import sys
ROOT=Path(__file__).resolve().parent
expected={
 'app/core/db.py':['TEAMROCKET_CLINICAL_OUTBOX_V1','activate(db)','drain(store, SessionLocal)'],
 'app/main.py':['drain_clinical_outbox','TEAMROCKET_CLINICAL_OUTBOX_V1'],
 'app/sync/worker.py':['receipt.get("status") not in {"ingested", "duplicate_ok"}',
                       'ingest_clinical_sync_event'],
 'app/cloud_completion/outbox.py':['class ClinicalCloudOutbox','def drain(','CLINICAL_TABLES'],
}
failed=0
for rel,markers in expected.items():
 p=ROOT/rel
 if not p.exists():
  print('FAIL: missing', rel);failed+=1;continue
 s=p.read_text(encoding='utf-8-sig')
 try:ast.parse(s)
 except SyntaxError as e:print('FAIL: syntax',rel,e);failed+=1;continue
 missing=[m for m in markers if m not in s]
 if missing:print('FAIL:',rel,'missing',missing);failed+=1
 else:print('PASS:',rel)
print('RESULT:', 'PASS (static only — cloud not verified)' if not failed else f'FAIL ({failed} file checks)')
sys.exit(bool(failed))
