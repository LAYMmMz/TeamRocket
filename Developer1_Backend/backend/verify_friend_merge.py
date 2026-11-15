"""Safe smoke checks in a temporary Dev1 SQLite Store and Dev2 clinical DB.
Run after integration: python verify_friend_merge.py
"""
import os
from pathlib import Path
import tempfile

with tempfile.TemporaryDirectory(prefix='teamrocket_verify_') as temp:
    os.environ['APP_ENV'] = 'test'
    os.environ['DEV2_DATABASE_URL'] = 'sqlite:///' + str(Path(temp)/'clinical.db').replace('\\','/')
    # Disable any real cloud attempt.
    os.environ['SYNC_RPC_URL'] = ''
    os.environ['SYNC_ACCESS_TOKEN'] = ''
    from fastapi.testclient import TestClient
    from app.core.config import Settings
    from app.main import create_app
    cfg=Settings(environment='test',sqlite_path=str(Path(temp)/'offline.db'),
                 sync_rpc_url='', sync_access_token='',
                 dev_auth_secret='development-test-secret-key-123456789012345',
                 offline_grant_secret='development-offline-secret-12345678901234')
    app=create_app(cfg)
    routes={r.path for r in app.routes}
    expected=['/api/health','/api/vitals','/api/radiation/personal-dose',
              '/api/environment/readings','/api/samples','/api/reports/{astronaut_id}',
              '/api/simulation/scenario']
    for route in expected:
        assert route in routes, 'Missing route: '+route
    with TestClient(app) as c:
        assert c.get('/api/health').status_code==200
        r=c.get('/api/vitals/CREW-01')
        assert r.status_code in (401,403),f'UNSAFE: unauthenticated vital read returned {r.status_code}'
        r=c.post('/api/simulation/reset')
        assert r.status_code in (401,403),f'UNSAFE: unauthenticated demo reset returned {r.status_code}'
    # Release pooled SQLite connections before Windows removes the temp directory.
    from app.core.db import engine
    engine.dispose()
    print('PASS: required Dev1 + friend Dev2 routes mounted')
    print('PASS: unverified requests cannot read Dev2 vitals or reset simulation')
    print('PASS: local startup and Dev2 tables work with temporary databases')
    print('NOT TESTED: clinical workflows, all 12 scenarios, cloud/RPC sync')
