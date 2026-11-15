"""TeamRocket development-only Dev2 synthetic symptom -> Dev1 Store bridge.
Run in Developer1_Backend/backend after stopping FastAPI.
Creates a .bak file; does not change databases or Supabase schema.
"""
from pathlib import Path
from datetime import datetime, timezone
import ast
import shutil
import sys

root = Path.cwd()
path = root / 'app' / 'vitals' / 'router.py'
if not path.exists():
    sys.exit('ERROR: Run from Developer1_Backend/backend')
src = path.read_text(encoding='utf-8')
marker = '    return {"id": symptom.id, "event_id": ev_id, "severity": payload.severity, "incident_id": incident_out}'
if '# TEAMROCKET_DEV2_SYMPTOM_CLOUD_V1' in src:
    sys.exit('Already installed. No changes made.')
if src.count(marker) != 1:
    sys.exit('ERROR: Expected symptom return statement not found exactly once. No changes made.')
insertion = '''    # TEAMROCKET_DEV2_SYMPTOM_CLOUD_V1
    # The Dev2 SQLAlchemy queue is local-only. Mirror the supported synthetic
    # symptom into Dev1's encrypted Store, whose worker uses the cloud RPC.
    # This does not enable cloud sync for unrelated Dev2 record types.
    store = db.info.get("store")
    settings = db.info.get("settings")
    if (
        store is not None
        and settings is not None
        and settings.environment in {"development", "test"}
        and payload.is_synthetic
        and payload.source_type == "SIMULATED"
    ):
        cloud_payload = {
            "event_id": ev_id,
            "mission_id": payload.mission_id,
            "astronaut_id": payload.astronaut_id,
            "symptom_code": payload.symptom_code,
            "symptom": payload.symptom_code,
            "severity": payload.severity,
            "onset_at": payload.onset_at.isoformat(),
            "body_location": payload.body_location,
            "measured_at": payload.measured_at.isoformat(),
            "recorded_at": payload.measured_at.isoformat(),
            "source_type": payload.source_type,
            "is_synthetic": True,
            "quality": "VALID",
            "verification": "UNVERIFIED",
            "source_reference": "dev2-synthetic-symptom-api",
            "source_revision": "v1",
        }
        store.put(
            "symptom", ev_id, cloud_payload,
            mission_id=payload.mission_id,
            actor_id=actor.user_id,
            priority=10,
        )

'''
updated = src.replace(marker, insertion + marker)
try:
    ast.parse(updated, filename=str(path))
except SyntaxError as e:
    sys.exit(f'ERROR: Syntax check failed: {e}')
backup = path.with_name(path.name + '.before_symptom_sync_' + datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S') + '.bak')
shutil.copy2(path, backup)
path.write_text(updated, encoding='utf-8')
print('PATCH INSTALLED:', path)
print('BACKUP:', backup)
print('Only /api/symptoms synthetic events are bridged. Restart FastAPI.')
