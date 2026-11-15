"""Backup-first source installer for TeamRocket merged Dev1+Dev2 backend.

Run from Developer1_Backend/backend. Never opens DB or modifies secrets.
Supports old cloud patch already installed, or first installation.
"""
from __future__ import annotations
import argparse
import ast
from datetime import datetime
from pathlib import Path
import shutil
import sys

BACKEND = Path.cwd()
APP = BACKEND / 'app'
MARK = 'TEAMROCKET_CLINICAL_OUTBOX_V1'
NEW = 'TEAMROCKET_UNIFIED_CLOUD_V2'


def once(src, old, new, description):
    if src.count(old) != 1:
        raise RuntimeError(f'{description}: expected exactly one anchor, got {src.count(old)}. No changes made.')
    return src.replace(old, new, 1)


def plan(source):
    required = ['app/main.py', 'app/core/db.py', 'app/sync/worker.py',
                'app/offline/store.py', 'app/models/dev2_models.py',
                'app/core/dev1_bridge.py', 'app/dev2_friend_attach.py']
    for path in required:
        if not (BACKEND / path).is_file():
            raise RuntimeError('Missing ' + path + ': run from the merged backend, not a fresh checkout')
    p = source / 'app/cloud_completion/outbox.py'
    if not p.is_file():
        raise RuntimeError('Missing new outbox.py in extracted patch folder')
    ast.parse(p.read_text(encoding='utf-8'), filename=str(p))
    files = {key: (BACKEND / key).read_text(encoding='utf-8-sig')
             for key in ['app/main.py', 'app/core/db.py', 'app/sync/worker.py']}
    if any(NEW in content for content in files.values()):
        raise RuntimeError('Unified V2 already installed. Refusing to apply twice.')
    installed = [(MARK in files[key]) for key in files]
    if any(installed) and not all(installed):
        raise RuntimeError('Partial previous cloud patch detected. Restore source backup first.')
    old_present = all(installed)
    if not old_present:
        db = files['app/core/db.py']
        db = once(db, 'from app.models.dev2_models import Base',
                  'from app.models.dev2_models import Base\n'
                  'from app.cloud_completion.outbox import activate, drain  # '+NEW,
                  'Dev2 get_db import')
        db = once(db, '    db = SessionLocal()\n    db.info["store"]',
                  '    db = SessionLocal()\n    activate(db)  # '+NEW+'\n    db.info["store"]',
                  'Dev2 get_db activation')
        db = once(db, '        yield db\n        db.commit()',
                  '        yield db\n        db.commit()\n'
                  '        store = db.info.get("store")\n'
                  '        if store is not None:\n'
                  '            drain(store, SessionLocal)  # '+NEW,
                  'Dev2 get_db drain')
        files['app/core/db.py'] = db
        main = files['app/main.py']
        main = once(main, '        app.state.store = Store(settings)',
                    '        app.state.store = Store(settings)\n'
                    '        from app.core.db import init_dev2_db, SessionLocal\n'
                    '        from app.cloud_completion.outbox import drain as drain_clinical_outbox\n'
                    '        init_dev2_db()\n'
                    '        drain_clinical_outbox(app.state.store, SessionLocal)  # '+NEW,
                    'Dev1 startup')
        files['app/main.py'] = main
    else:
        # Previous patch had valid transaction-coupled queue hooks; keep them.
        files['app/main.py'] += '\n# '+NEW+': unified RPC integration enabled\n'
        files['app/core/db.py'] += '\n# '+NEW+': unified RPC integration enabled\n'
    worker = files['app/sync/worker.py']
    if old_present:
        start = worker.find('            endpoint = self.url\n')
        end = worker.find('            response.raise_for_status()', start)
        if start < 0 or end < 0:
            raise RuntimeError('Previous worker routing anchor missing. No changes made.')
        block = worker[start:end]
        if 'ingest_clinical_sync_event' not in block:
            raise RuntimeError('Unexpected previous cloud transport. No changes made.')
        worker = worker[:start] + '''            response = client.post(
                self.url, json={"p_event": event}, headers=headers
            )  # '''+NEW+'\n' + worker[end:]
        # Old strict receipt check is already present.
    else:
        worker = once(worker,
            '                if not isinstance(receipt, dict) or (\n',
            '                if not isinstance(receipt, dict) or (\n'
            '                    receipt.get("status") not in {"ingested", "duplicate_ok"}\n'
            '                    or ', 'worker strict receipt validation')
    # Original fake-cloud MemoryReceiptTransport used no status. Keep isolated tests working.
    # This does not weaken live validation: only successful simulated receipts get status.
    needle = '        receipt = {\n            "event_id": event["event_id"],'
    if needle in worker:
        worker = once(worker, needle,
                      '        receipt = {\n            "status": "ingested",\n            "event_id": event["event_id"],',
                      'memory transport status')
    worker += '\n# '+NEW+': accepts ingested/duplicate_ok only; one RPC endpoint\n'
    files['app/sync/worker.py'] = worker
    for rel, content in files.items():
        ast.parse(content, filename=rel)
    return files, p, old_present


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source', required=True, help='Extracted TeamRocket_Unified_Cloud_Patch_V2 folder')
    args=parser.parse_args()
    source=Path(args.source).expanduser().resolve()
    if not source.is_dir():
        print('NOT INSTALLED: source folder not found:', source)
        return 2
    try:
        files,outbox,old = plan(source)
    except Exception as exc:
        print('NOT INSTALLED:',exc)
        return 2
    target = APP / 'cloud_completion/outbox.py'
    if target.is_file() and not old:
        print('NOT INSTALLED: existing outbox without recognized V1 hooks; refusing overwrite')
        return 2
    original = dict(files)
    original = {path:(BACKEND/path).read_bytes() for path in files}
    backup=BACKEND/('_unified_cloud_source_backup_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    backup.mkdir(parents=True,exist_ok=False)
    for rel in files:
        dest=backup/rel; dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(original[rel])
    if target.is_file():
        dest=backup/'app/cloud_completion/outbox.py';dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(target,dest)
    try:
        target.parent.mkdir(parents=True,exist_ok=True)
        (target.parent/'__init__.py').touch()
        shutil.copy2(outbox,target)
        for rel,content in files.items():
            (BACKEND/rel).write_text(content,encoding='utf-8')
    except Exception:
        for rel,contents in original.items():
            (BACKEND/rel).write_bytes(contents)
        if old:
            shutil.copy2(backup/'app/cloud_completion/outbox.py',target)
        else:
            target.unlink(missing_ok=True)
        raise
    print('INSTALLED unified cloud V2. Previous patch:', 'detected' if old else 'absent')
    print('Source backup:', backup)
    print('No databases or .env files were modified.')
    print('Existing V1 clinical_record queue items require separate review; do not treat them as synced.')
    return 0


if __name__=='__main__':
    sys.exit(main())
