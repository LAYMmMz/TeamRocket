"""Install additive TeamRocket clinical outbox + fix Dev1 sync receipt validation.

Run from existing Developer1_Backend/backend, AFTER the friend merge.
No databases are modified by the installer. Source backup is created first.
"""
from __future__ import annotations
import ast
import argparse
from datetime import datetime
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
BACKEND = HERE
SOURCE_DIR = None
APP = BACKEND / 'app'
BACKUP = BACKEND / ('_cloud_completion_source_backup_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
MARK = 'TEAMROCKET_CLINICAL_OUTBOX_V1'


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def mutate(original, old, new, path):
    require(original.count(old) == 1, f'{path}: expected exactly one integration anchor; found {original.count(old)}. No files changed.')
    return original.replace(old, new, 1)


def create_changes():
    require((APP / 'offline' / 'store.py').is_file(), 'Run inside the existing Dev1 backend folder.')
    require((APP / 'core' / 'dev1_bridge.py').is_file(), 'Friend Dev2 merge missing. Install and verify friend merge first.')
    require((APP / 'models' / 'dev2_models.py').is_file(), 'Friend Dev2 models missing.')
    require((APP / 'dev2_friend_attach.py').is_file(), 'Friend Dev2 attachment missing.')
    require((APP / 'cloud_completion' / 'outbox.py').exists() is False, 'Clinical outbox module already exists; refusing overwrite.')
    paths = ['app/core/db.py', 'app/main.py', 'app/sync/worker.py']
    files = {p: (BACKEND / p).read_text(encoding='utf-8-sig') for p in paths}
    for p, content in files.items():
        require(MARK not in content, f'{p} already modified; refusing double-install.')

    p = 'app/core/db.py'
    src = files[p]
    src = mutate(src,
        'from app.models.dev2_models import Base',
        'from app.models.dev2_models import Base\n'
        'from app.cloud_completion.outbox import ClinicalCloudOutbox, activate, drain  # '+MARK,
        p)
    src = mutate(src,
        '    db = SessionLocal()\n    db.info["store"]',
        '    db = SessionLocal()\n    activate(db)  # '+MARK+'\n    db.info["store"]',p)
    src = mutate(src,
        '        yield db\n        db.commit()',
        '        yield db\n        db.commit()\n'
        '        store = db.info.get("store")\n'
        '        if store is not None:\n'
        '            drain(store, SessionLocal)  # '+MARK,p)
    files[p] = src

    p = 'app/main.py'
    src = files[p]
    src = mutate(src,
        '        app.state.store = Store(settings)',
        '        app.state.store = Store(settings)\n'
        '        # Replay committed Dev2 clinical outbox records after a crash or restart.\n'
        '        from app.core.db import init_dev2_db, SessionLocal\n'
        '        from app.cloud_completion.outbox import drain as drain_clinical_outbox\n'
        '        init_dev2_db()\n'
        '        drain_clinical_outbox(app.state.store, SessionLocal)  # '+MARK,p)
    files[p] = src

    p = 'app/sync/worker.py'
    src = files[p]
    src = mutate(src,
        'import hashlib',
        'import hashlib\nimport os  # '+MARK,p)
    src = mutate(src,
        '            response = client.post(\n                self.url, json={"p_event": event}, headers=headers\n            )',
        '            endpoint = self.url\n'
        '            if event.get("kind") == "clinical_record":\n'
        '                endpoint = os.getenv("SYNC_CLINICAL_RPC_URL", "").strip()\n'
        '                if not endpoint and self.url.endswith("/ingest_sync_event"):\n'
        '                    endpoint = self.url[:-len("/ingest_sync_event")] + "/ingest_clinical_sync_event"\n'
        '                if not endpoint or not endpoint.startswith("https://"):\n'
        '                    raise AppError(503,"clinical_cloud_not_configured", "Clinical Supabase RPC not configured")\n'
        '            response = client.post(\n                endpoint, json={"p_event": event}, headers=headers\n            )  # '+MARK,p)
    src = mutate(src,
        '                if not isinstance(receipt, dict) or (',
        '                if not isinstance(receipt, dict) or (\n'
        '                    receipt.get("status") not in {"ingested", "duplicate_ok"}\n'
        '                    or ',p)
    files[p] = src
    for p, text in files.items():
        ast.parse(text, filename=p)
    cloud_file = SOURCE_DIR / 'app/cloud_completion/outbox.py'
    require(cloud_file.exists(), 'Missing patch file app/cloud_completion/outbox.py')
    ast.parse(cloud_file.read_text(encoding='utf-8'), filename=str(cloud_file))
    return files


def main():
    global SOURCE_DIR
    parser = argparse.ArgumentParser(description='Install TeamRocket additive cloud patch')
    parser.add_argument('--source', required=True, help='Extracted TeamRocket_Cloud_Completion_Patch folder')
    args = parser.parse_args()
    SOURCE_DIR = Path(args.source).expanduser().resolve()
    if not SOURCE_DIR.is_dir():
        print('NOT INSTALLED: missing source folder', SOURCE_DIR)
        return 2
    try:
        changes = create_changes()
    except Exception as exc:
        print('NOT INSTALLED:',exc)
        return 2
    BACKUP.mkdir(parents=True)
    for relpath in changes:
        target = BACKEND / relpath
        dest = BACKUP / relpath
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, dest)
    touched = []
    try:
        target_dir = APP / 'cloud_completion'
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / '__init__.py').write_text('', encoding='utf-8')
        shutil.copy2(SOURCE_DIR / 'app/cloud_completion/outbox.py', target_dir / 'outbox.py')
        touched.append(target_dir / 'outbox.py')
        for relpath, content in changes.items():
            target = BACKEND / relpath
            target.write_text(content, encoding='utf-8')
            touched.append(target)
    except Exception:
        for relpath in changes:
            shutil.copy2(BACKUP / relpath, BACKEND / relpath)
        for item in touched:
            if item.name == 'outbox.py':
                item.unlink(missing_ok=True)
        raise
    print('INSTALLED: clinical outbox + strict Dev1 receipt validation.')
    print('Backup:', BACKUP)
    print('Cloud migration NOT applied. You must deploy it to your test Supabase separately.')
    return 0

if __name__ == '__main__':
    sys.exit(main())
