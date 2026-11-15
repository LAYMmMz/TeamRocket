"""Idempotent and backed-up installer; run inside Developer1_Backend/backend."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent
MAIN=ROOT/'app'/'main.py'
PACKAGE=ROOT/'app'/'domain2'
if not MAIN.exists() or not (PACKAGE/'router.py').exists():
    raise SystemExit('Expected existing backend/app/main.py and app/domain2/router.py')
s=MAIN.read_text(encoding='utf-8')
if 'Dev2 modular domain routers' in s:
    print('Already installed; no modification');raise SystemExit(0)
anchor='    return app\n'
if s.count(anchor)!=1:
    raise SystemExit('Unexpected main.py structure; no changes made')
patch='''    # Dev2 modular domain routers (prototype only; secure Dev1 Store retained).
    from app.domain2.router import router as dev2_domain
    from app.domain2.reports import router as dev2_reports
    from app.domain2.baselines import router as dev2_baselines
    from app.domain2.vitals import router as dev2_vitals
    for added_router in [dev2_domain, dev2_reports, dev2_baselines, dev2_vitals]:
        app.include_router(added_router, prefix="/api")

'''
backup=ROOT/'app'/'main.before_dev2_integration.py.bak'
if backup.exists():
    raise SystemExit('Backup already exists; no changes made. Inspect manually.')
shutil.copy2(MAIN,backup)
MAIN.write_text(s.replace(anchor,patch+anchor,1),encoding='utf-8')
print('Installed developer 2 prototype routers. Backup:',backup)
