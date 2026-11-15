"""Registers friend Dev2 demo routes into the existing Dev1 FastAPI app.
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

def attach_dev2(app, settings):
    if settings.environment not in {'development', 'test'}:
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
