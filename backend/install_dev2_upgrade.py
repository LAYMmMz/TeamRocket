"""Run inside existing Developer1_Backend/backend AFTER copying new app/domain2 files.

Idempotent: attaches only newly added routers; never replaces previous routes.
"""
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parent
MAIN=ROOT/'app'/'main.py'
if not MAIN.exists() or not (ROOT/'app'/'domain2'/'analysis.py').exists():
    raise SystemExit('Expected backend/app/main.py and app/domain2/analysis.py. Check copied folders.')
s=MAIN.read_text(encoding='utf-8')
marker='# TeamRocket Dev2 domain analysis + dashboard routers'
if marker in s:
    print('Dev 2 upgrade already installed; no changes.');raise SystemExit(0)
anchor='    return app\n'
if s.count(anchor)!=1:
    raise SystemExit('Could not safely find app factory return; no files changed.')
patch='''    # TeamRocket Dev2 domain analysis + dashboard routers
    from app.domain2.analysis import router as dev2_analysis_router
    from app.domain2.dashboards import router as dev2_dashboard_router
    app.include_router(dev2_analysis_router, prefix="/api")
    app.include_router(dev2_dashboard_router, prefix="/api")

'''
backup=ROOT/'app'/'main.before_dev2_upgrade.py.bak'
if backup.exists():
    raise SystemExit(f'Backup {backup.name} already exists. Inspect it before rerunning.')
shutil.copy2(MAIN,backup)
MAIN.write_text(s.replace(anchor,patch+anchor,1),encoding='utf-8')
print('Dev 2 upgrade routes installed. Original main.py backed up to:',backup)
