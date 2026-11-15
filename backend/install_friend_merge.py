"""Safe, pinned-source Dev2 merge for existing TeamRocket Dev1 backend.
Requires Internet to retrieve exact GitHub source files. Keeps Dev1 code/data intact.
"""
from __future__ import annotations

import ast
import datetime
import importlib.util
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent
APP = ROOT / 'app'
MAIN = APP / 'main.py'
PIN = '89e78796c5fb447f390d89f9282fe226fa0774b0'
BASE_URL = 'https://raw.githubusercontent.com/LAYMmMz/TeamRocket/' + PIN + '/dev2integrated/'
MODULE_DIRS = ['vitals','radiation','environment','wellness','examinations','samples','reports','nasa','seed','simulation']
FILES = [
    'app/config.py',
    'app/core/db.py', 'app/core/dev1_bridge.py',
    'app/db/session.py', 'app/models/dev2_models.py', 'app/schemas/dev2_schemas.py',
    'app/vitals/router.py', 'app/vitals/service.py',
    'app/radiation/router.py', 'app/radiation/service.py',
    'app/environment/router.py', 'app/environment/service.py',
    'app/wellness/router.py', 'app/wellness/service.py',
    'app/examinations/router.py', 'app/examinations/service.py',
    'app/samples/router.py', 'app/samples/service.py',
    'app/reports/router.py', 'app/reports/service.py',
    'app/nasa/router.py',
    'app/seed/seed_demo.py', 'app/seed/scenarios.py',
    'app/simulation/router.py',
]
MARKER = 'TEAMROCKET_PINNED_FRIEND_DEV2_MERGE_V1'

def fail(message):
    raise SystemExit('STOP: ' + message)

def load_source(path):
    local = ROOT / 'dev2integrated' / path
    if local.is_file():
        return local.read_text(encoding='utf-8-sig')
    url = BASE_URL + path
    request = urllib.request.Request(url, headers={'User-Agent': 'TeamRocket-Dev2-Integration/1.0'})
    try:
        with urllib.request.urlopen(request, timeout=35) as res:
            b = res.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        fail(f'Cannot download {path} from GitHub. Check Internet access. Detail: {exc}')
    if len(b) < 20 or len(b) > 500_000:
        fail('Unexpected file size for ' + path)
    return b.decode('utf-8-sig')

def patch(path, source):
    if path == 'app/core/db.py':
        old = 'DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("DEV2_DATABASE_URL") or DEFAULT_SQLITE_URL'
        new = '''# Dev2 storage is a separate LOCAL PROTOTYPE database; never auto-create Supabase tables.
DATABASE_URL = os.getenv("DEV2_DATABASE_URL") or DEFAULT_SQLITE_URL
if not DATABASE_URL.startswith("sqlite:///"):
    raise RuntimeError("Dev2 must use a local SQLite URL; cloud integration requires reviewed migrations")'''
        if source.count(old) != 1: fail('Friend DB config changed upstream; manual review required')
        source = source.replace(old, new)
    elif path == 'app/core/dev1_bridge.py':
        beginning = source.index('def get_actor_context(')
        ending = source.index('\n\nclass Dev1IntegrationBridge:', beginning)
        secure = '''def get_actor_context(request: Request, principal=Depends(current_principal)) -> ActorContext:
    """Use the SAME verified Dev1 JWT as the original API; never trust role headers."""
    role = (principal.roles[0] if principal.roles else "crew").upper()
    return ActorContext(user_id=principal.user_id, role=role,
                        astronaut_id=getattr(principal, "astronaut_id", None),
                        mission_ids=list(principal.mission_ids))'''
        source = source[:beginning] + secure + source[ending:]
        # Use Dev1's real audited event method, not a fabricated `audit_logs` queue kind.
        a = source.index('    def record_audit(')
        b = source.index('    def enforce_behavioral_privacy(', a)
        section = source[a:b]
        marker = '        store = db.info.get("store")'
        if section.count(marker) != 1: fail('Friend audit bridge changed; manual review required')
        start = section.index(marker)
        end = section.index('        return entry', start)
        section = section[:start] + '''        store = db.info.get("store")
        if store is not None:
            store.audit(action, actor.user_id, details={
                "role": actor.role, "resource_type": resource_type,
                "resource_id": resource_id, "outcome": outcome,
            })
''' + section[end:]
        source = source[:a] + section + source[b:]
        injected = 'from fastapi import Depends\nfrom app.auth.dependencies import current_principal\n'
        if source.startswith('from __future__ import annotations\n'):
            source = source.replace('from __future__ import annotations\n', 'from __future__ import annotations\n' + injected, 1)
        else:
            source = injected + source
        # Prevent the Dev2 prototype from enqueueing unsupported kinds into Dev1's real cloud queue.
        beg = source.index('    def enqueue_sync(')
        end = source.index('\n    @staticmethod', beg+1)
        part = source[beg:end]
        if 'store = db.info.get("store")' not in part: fail('Friend queue bridge changed; manual review required')
        part = part.replace('store = db.info.get("store")', 'store = None  # Safe local-only Dev2 queue; NO cloud receipts')
        source = source[:beg] + part + source[end:]
        # Alerts/incidents belong to a Dev2 demo projection, not Dev1's validated medical engine.
        beg = source.index('    def emit_alert_and_optional_incident(')
        end = source.index('\n    @classmethod', beg+1)
        part = source[beg:end]
        if 'store = db.info.get("store")' not in part: fail('Friend alert bridge changed; manual review required')
        part = part.replace('store = db.info.get("store")', 'store = None  # Never bypass Dev1 official alert and incident engine')
        source = source[:beg] + part + source[end:]
    elif path == 'app/seed/seed_demo.py':
        beg = source.index('def _populate_dev1_store(')
        end = source.index('\ndef run_seed(', beg)
        # Keep seed/reset within dedicated Dev2 demo DB, never rewrite Dev1's protected records.
        source = source[:beg] + '''def _populate_dev1_store(store, rng):
    """No-op: isolated Dev2 demo must never mutate Dev1's authoritative store."""
    return None

''' + source[end:]
    elif path == 'app/seed/scenarios.py':
        if 'def execute_scenario(' not in source: fail('Friend scenario entrypoint changed')
        if 'def run_scenario(' not in source:
            source += '\n\n# Compatibility with the committed simulation router.\nrun_scenario = execute_scenario\n'
    return source

ATTACH_CODE = '''"""Registers friend Dev2 demo routes into the existing Dev1 FastAPI app.
Development/test only; Dev1 auth, storage and cloud sync remain authoritative.
"""
from __future__ import annotations
from fastapi import Depends, Request
from app.auth.dependencies import require
from app.core.db import init_dev2_db

MODULES = [
    'app.vitals.router', 'app.radiation.router', 'app.environment.router',
    'app.wellness.router', 'app.examinations.router', 'app.samples.router',
    'app.reports.router', 'app.nasa.router', 'app.simulation.router',
]

async def dev2_guard(request: Request, principal=Depends(require('measurements:write'))):
    # All Dev2 API calls need the verified Dev1 JWT and mission permission.
    # The friend project is a synthetic demo; no production use.
    mission = request.query_params.get('mission_id')
    if request.method in {'POST', 'PUT', 'PATCH'}:
        try:
            data = await request.json()
        except (ValueError, UnicodeDecodeError):
            data = None
        if isinstance(data, dict) and data.get('mission_id'):
            mission = str(data['mission_id'])
    principal.require_mission(mission or 'DEMO-01')
    return principal

def attach_dev2(app):
    if app.state.settings.environment not in {'development', 'test'} if hasattr(app.state, 'settings') else False:
        return
    # The friend Dev2 SQLAlchemy models must stay strictly in a local SQLite DB.
    init_dev2_db()
    from importlib import import_module
    for module_name in MODULES:
        module = import_module(module_name)
        router = module.router
        routes = [getattr(r, 'path', '') for r in router.routes]
        prefix = '' if any(path.startswith('/api/') for path in routes) else '/api'
        app.include_router(router, prefix=prefix, dependencies=[Depends(dev2_guard)])
'''
# Patched below to use Settings argument during create_app, not app.state before lifespan.
ATTACH_CODE = ATTACH_CODE.replace('def attach_dev2(app):\n    if app.state.settings.environment not in {\'development\', \'test\'} if hasattr(app.state, \'settings\') else False:',
                                  'def attach_dev2(app, settings):\n    if settings.environment not in {\'development\', \'test\'}:')

def main():
    if not MAIN.is_file() or not (APP / 'offline' / 'store.py').exists():
        fail('Place this installer directly in your existing Developer1_Backend/backend folder')
    original = MAIN.read_text(encoding='utf-8-sig')
    if MARKER in original:
        print('Already installed. No modifications made.');return
    if original.count('    return app') != 1 or 'def create_app(' not in original:
        fail('Cannot safely patch this customized app/main.py. Original files untouched.')
    if 'app/main.py' in FILES or any((APP / x).exists() for x in ('core/db.py','core/dev1_bridge.py')):
        fail('Friend bridge/core/db already exists. Review existing versions before installing.')
    for lib in ['sqlalchemy','pydantic_settings','httpx','fastapi']:
        if importlib.util.find_spec(lib) is None:
            fail(f'Missing dependency {lib}. Run: python -m pip install sqlalchemy pydantic-settings')
    print('Downloading pinned friend Dev2 source; existing Dev1 files will not be replaced...')
    with tempfile.TemporaryDirectory(prefix='teamrocket_friend_') as t:
        temp = Path(t)
        for path in FILES:
            source = patch(path, load_source(path))
            try: ast.parse(source, filename=path)
            except SyntaxError as exc: fail(f'Friend source syntax error in {path}: {exc}')
            target = temp / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source, encoding='utf-8')
        for folder in ['app/db','app/models','app/schemas',*(f'app/{d}' for d in MODULE_DIRS)]:
            f = temp / folder / '__init__.py'; f.parent.mkdir(parents=True, exist_ok=True)
            if not f.exists():f.write_text('',encoding='utf-8')
        file = temp/'app/dev2_friend_attach.py';file.write_text(ATTACH_CODE,encoding='utf-8');ast.parse(ATTACH_CODE)
        # Replace nothing in Dev1. If a file exists in the target, stop.
        conflict = [p for p in temp.rglob('*') if p.is_file() and (ROOT/p.relative_to(temp)).exists()]
        if conflict:
            fail('These paths already exist (none overwritten): '+', '.join(str(x.relative_to(temp)) for x in conflict[:8]))
        line = f'''    # {MARKER}: friend Dev2 clinical demo, isolated from official sync.
    from app.dev2_friend_attach import attach_dev2
    attach_dev2(app, settings)
'''
        # Insert before old domain2 routes so friend's endpoints take precedence.
        old_marker = '    # Dev2 modular domain routers'
        if old_marker in original:
            changed = original.replace(old_marker, line+'\n'+old_marker,1)
        else:
            changed = original.replace('    return app',line+'    return app',1)
        # Earlier prototype routes would shadow the friend's canonical vitals/reports paths.
        old_loop = 'for added_router in [dev2_domain, dev2_reports, dev2_baselines, dev2_vitals]:'
        if old_loop in changed:
            changed = changed.replace(old_loop, 'for added_router in [dev2_domain, dev2_baselines]:', 1)
        ast.parse(changed, filename='app/main.py')
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup = ROOT / f'app/main.before_friend_merge_{timestamp}.py.bak'
        shutil.copy2(MAIN, backup)
        try:
            for p in temp.rglob('*'):
                if p.is_file():
                    dest=ROOT/p.relative_to(temp)
                    dest.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copy2(p,dest)
            MAIN.write_text(changed,encoding='utf-8')
        except Exception:
            shutil.copy2(backup, MAIN)
            raise
        print('Installed friend Dev2 modules into existing app/; Dev1 files preserved.')
        print('Main backup:',backup)
        print('DEMO ONLY. Separate clinical DB: data/dev2_clinical.db')
        print('Restart: python dev.py  |  Check: http://127.0.0.1:8000/docs')
        print('Do not enable Supabase for Dev2 data; waiting for reviewed RPC schema.')
if __name__=='__main__':main()
