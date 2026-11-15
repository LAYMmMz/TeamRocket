"""TeamRocket one-go REAL backend/cloud acceptance smoke test.
Run from Developer1_Backend/backend, with FastAPI running and test-user permission.
Only creates synthetic records. Never reveals or persists credentials.
"""
from __future__ import annotations
import argparse, getpass, json, os, pathlib, subprocess, sys, time, uuid
from datetime import datetime, timezone
from urllib import request, error, parse

ROOT = pathlib.Path.cwd()
RESULTS = []

def log(name, state, detail=''):
    RESULTS.append({'test':name,'status':state,'detail':str(detail)[:900]})
    print(f'[{state}] {name}' + (f' — {str(detail)[:220]}' if detail else ''),flush=True)

def load_env():
    f=ROOT/'.env'
    if not f.exists():
        log('Local .env exists','BLOCKED','Expected Developer1_Backend/backend/.env')
        return
    for line in f.read_text(encoding='utf-8-sig').splitlines():
        line=line.strip()
        if not line or line.startswith('#') or '=' not in line: continue
        k,v=line.split('=',1);k=k.strip()
        if not k.isidentifier(): continue
        os.environ.setdefault(k,v.strip().strip('"').strip("'"))

def http(method, url, data=None, headers=None, timeout=20):
    hd={'Accept':'application/json',**(headers or {})}
    body=None
    if data is not None:
        body=json.dumps(data,default=str).encode('utf-8')
        hd['Content-Type']='application/json'
    req=request.Request(url,body,headers=hd,method=method)
    try:
        with request.urlopen(req,timeout=timeout) as r:
            payload=r.read(); status=r.status
    except error.HTTPError as e:
        status=e.code;payload=e.read()
    except Exception as e:
        return 0,{'error':type(e).__name__+': '+str(e)[:230]}
    try:return status,json.loads(payload)
    except ValueError:return status,{'text':payload.decode(errors='replace')[:500]}

def cloud_rows(base,key,token,table,select,filters):
    query={'select':select,**filters}
    url=base.rstrip('/')+'/rest/v1/'+table+'?'+parse.urlencode(query)
    return http('GET',url,headers={'apikey':key,'Authorization':'Bearer '+token})

def get_token(base,key):
    existing=os.getenv('SYNC_ACCESS_TOKEN','').strip()
    if existing:
        status,profile=http('GET',base+'/auth/v1/user',headers={'apikey':key,'Authorization':'Bearer '+existing})
        if status==200:
            log('Supabase test JWT valid','PASS','Authenticated user token accepted')
            return existing
        log('Existing sync JWT','BLOCKED','Expired/invalid; enter test-user credentials to refresh')
    email=input('Supabase AUTH test-user email: ').strip()
    password=getpass.getpass('Supabase AUTH test-user password (hidden): ')
    status,data=http('POST',base+'/auth/v1/token?grant_type=password',{'email':email,'password':password},headers={'apikey':key})
    password=None
    token=data.get('access_token') if isinstance(data,dict) else None
    if status!=200 or not token:
        log('Supabase user login','FAIL',f'HTTP {status}, {data.get("error_description") or data.get("msg") or data.get("error") if isinstance(data,dict) else "invalid response"}')
        return None
    log('Supabase test JWT valid','PASS','Signed in with Supabase Auth')
    return token

def api_token():
    try:
        from app.auth.dependencies import issue_development_token
        from app.core.config import Settings
        s=Settings()
        return issue_development_token(s,'verification-local-'+uuid.uuid4().hex[:8],['flight_surgeon'],['DEMO-02'])
    except Exception as exc:
        log('FastAPI development test token','BLOCKED',f'{type(exc).__name__}: {exc}; ensure APP_ENV=development and DEV_AUTH_SECRET is set')
        return None

def receipt_id_from_created(data):
    if not isinstance(data,dict): return None
    m=data.get('measurement',data)
    if not isinstance(m,dict):return None
    return m.get('id') or m.get('record_id')

def receipt_probe(base,headers,kind,rid):
    if not rid: return None
    status,response=http('GET',base+'/api/sync/receipts/'+parse.quote(kind,safe='')+'/'+parse.quote(str(rid),safe=''),headers=headers)
    return (status,response)

def check_receipt(cloud,key,token,event_id,kind,table,field,expected):
    cs,rows=cloud_rows(cloud,key,token,'sync_receipts','event_id,receipt_id,record_id,payload_hash,kind,mission_id',{'event_id':'eq.'+event_id})
    good=cs==200 and isinstance(rows,list) and len(rows)==1 and rows[0].get('kind')==kind
    log(kind+' Supabase receipt','PASS' if good else 'FAIL',f'HTTP {cs}; matched={len(rows) if isinstance(rows,list) else "error"}; event={event_id}')
    if not good:return False
    record_id=str(rows[0].get('record_id'))
    try:
        target_uuid=str(uuid.UUID(record_id))
    except Exception:
        import hashlib
        target_uuid=str(uuid.UUID(hashlib.md5((kind+':'+record_id).encode()).hexdigest()))
    cs,data=cloud_rows(cloud,key,token,table,'id,mission_id,'+field,{'id':'eq.'+target_uuid})
    matched=cs==200 and isinstance(data,list) and len(data)==1 and data[0].get('mission_id')=='DEMO-02' and (str(data[0].get(field))==str(expected))
    log(kind+' cloud record readback','PASS' if matched else 'FAIL',f'HTTP {cs}; rows={data if cs==200 else "permission/error"}')
    return matched

def scenario_tests():
    targets=['tests/test_dev2_suite.py','tests/test_integrated_suite.py']
    present=[x for x in targets if (ROOT/x).is_file()]
    if not present:
        log('S01–S12 scenario suite','BLOCKED','Neither expected test file is present in this backend folder')
        return
    try:
        cmd=[sys.executable,'-m','pytest','-q',*present]
        # Don't use -s or echo env, and cap execution time
        p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=140,env=os.environ.copy())
        excerpt='\n'.join((p.stdout+'\n'+p.stderr).splitlines()[-12:])[:1100]
        log('S01–S12 scenario suite','PASS' if p.returncode==0 else 'FAIL',excerpt)
    except subprocess.TimeoutExpired:
        log('S01–S12 scenario suite','FAIL','Timed out after 140 seconds')
    except Exception as e:
        log('S01–S12 scenario suite','BLOCKED',str(e))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--base',default='http://127.0.0.1:8000')
    parser.add_argument('--skip-scenarios',action='store_true')
    args=parser.parse_args()
    load_env()
    base=args.base.rstrip('/')
    cloud=os.getenv('SUPABASE_URL','').strip().rstrip('/')
    key=os.getenv('SUPABASE_ANON_KEY','').strip()
    rpc=os.getenv('SYNC_RPC_URL','').strip()
    if not cloud or not key or key.startswith('sb_secret_') or key.startswith('sb_secret'):
        log('Supabase publishable configuration','BLOCKED','SUPABASE_URL + SUPABASE_ANON_KEY must be set to URL + publishable/anon key, not sb_secret')
        return finish()
    if not rpc:log('Sync RPC configured in this terminal','BLOCKED','Set SYNC_RPC_URL in the terminal that starts FastAPI')
    token=get_token(cloud,key)
    if not token:return finish()
    status,health=http('GET',base+'/api/health')
    if status!=200:
        log('FastAPI running','FAIL',f'HTTP {status}: {health}');return finish()
    log('FastAPI running','PASS',f'HTTP 200; cloud_sync_configured={health.get("cloud_sync_configured")}')
    if health.get('cloud_sync_configured') is False:
        log('Server-side cloud worker configuration','BLOCKED','Restart FastAPI from original login terminal with SYNC_ACCESS_TOKEN and SYNC_RPC_URL set')
        return finish()
    local=api_token()
    if not local:return finish()
    headers={'Authorization':'Bearer '+local}
    status,session=http('GET',base+'/api/auth/session',headers=headers)
    if status!=200:
        log('Backend role/mission authorization','FAIL',f'HTTP {status}: {session}');return finish()
    log('Backend role/mission authorization','PASS','flight_surgeon DEMO-02')
    stamp=datetime.now(timezone.utc).isoformat()
    uuidstr=str(uuid.uuid4()); evt='onego-'+uuidstr
    payload={'event_id':evt,'mission_id':'DEMO-02','astronaut_id':'TEST-CREW-01','source_type':'SIMULATED','is_synthetic':True,'measured_at':stamp,'quality':'VALID','verification':'UNVERIFIED','source_reference':'teamrocket-one-go','source_revision':'1','metric':'heart_rate','value':72,'unit':'bpm','metadata':{'test_tag':evt}}
    status,created=http('POST',base+'/api/measurements',payload,headers)
    if status!=201:
        log('Create Dev1 measurement through FastAPI','FAIL',f'HTTP {status} {created}');return finish()
    log('Create Dev1 measurement through FastAPI','PASS',f'HTTP 201, event {evt}')
    rid=receipt_id_from_created(created)
    ds=0
    for n in range(3):
        s,r=http('POST',base+'/api/sync/run',{},headers)
        if s!=200:
            log('Run backend sync worker','FAIL',f'HTTP {s}, {r}');break
        ds+=r.get('delivered',0)
        if ds:break
        time.sleep(1)
    else: log('Run backend sync worker','BLOCKED','Delivered=0, may have been background synced; cloud receipt readback decides')
    if ds:log('Run backend sync worker','PASS',f'delivered={ds}; may include other queued events')
    # Dev1 local event_id is remote_event_id = measurement:<record_id>, which can differ from input event ID
    # First attempt to obtain queued ID via locally returned record ID, but don't assume response id exists.
    remote_event='measurement:'+str(rid or evt)
    confirmed=False
    for _ in range(5):
        cs,rows=cloud_rows(cloud,key,token,'sync_receipts','event_id',{'event_id':'eq.'+remote_event})
        if cs==200 and isinstance(rows,list) and rows: confirmed=True; break
        time.sleep(1)
    check_receipt(cloud,key,token,remote_event,'measurement','health_logs','metric_code','heart_rate')

    # Dev2: use live API schema; unknown required fields are never guessed.
    s,spec=http('GET',base+'/openapi.json')
    if s!=200 or not isinstance(spec,dict):
        log('Dev2 API discovery','BLOCKED','OpenAPI unavailable')
    else:
        paths=spec.get('paths',{})
        candidates=[(p, v['post']) for p,v in paths.items() if isinstance(v,dict) and 'post' in v and ('symptom' in p.lower() or 'symptom' in (v['post'].get('summary') or '').lower())]
        if not candidates:
            log('Dev2 symptom API','BLOCKED','No symptom POST endpoint found in running FastAPI/OpenAPI')
        else:
            # Use explicit input only when the route's schema supports those fields.
            p,op=candidates[0]
            schema=op.get('requestBody',{}).get('content',{}).get('application/json',{}).get('schema',{})
            ref=schema.get('$ref',''); name=ref.rsplit('/',1)[-1]
            resolved=spec.get('components',{}).get('schemas',{}).get(name,schema)
            props=resolved.get('properties',{});required=set(resolved.get('required',[]))
            usable={'event_id':'symptom-'+str(uuid.uuid4()),'mission_id':'DEMO-02','astronaut_id':'TEST-CREW-01',
                    'crew_code':'TEST-CREW-01','symptom_code':'headache','severity':'mild','notes':'Synthetic one-go cloud test',
                    'onset_at':stamp,'reported_at':stamp,'measured_at':stamp,'recorded_at':stamp,'timestamp':stamp,
                    'source_type':'SIMULATED','is_synthetic':True,'source_reference':'teamrocket-one-go','source_revision':'1',
                    'quality':'VALID','verification':'UNVERIFIED','body_location':'head','visibility_classification':'CLINICAL_TEAM'}
            unknown=required-set(usable)
            if unknown or not props:
                log('Dev2 symptom API','BLOCKED',f'Found {p} but schema needs fields not safely inferred: {sorted(unknown)}; open API and use test form')
            else:
                body={k:v for k,v in usable.items() if k in props}
                st,ans=http('POST',base+p,body,headers)
                if st not in (200,201):
                    log('Create Dev2 symptom through FastAPI','FAIL',f'{p} HTTP {st}: {ans}')
                else:
                    log('Create Dev2 symptom through FastAPI','PASS',f'{p} HTTP {st}')
                    s,r=http('POST',base+'/api/sync/run',{},headers)
                    log('Run Dev2 clinical sync worker','PASS' if s==200 else 'FAIL',f'HTTP {s}; {r if s==200 else ans}')
                    # Resolve source record by dedicated marker when possible; due to outbox v2 mapping,
                    # cloud event ID is deterministic and not equal to input event ID.
                    st,rows=cloud_rows(cloud,key,token,'clinical_records','id,record_kind,mission_id,clinical_payload',
                                       {'record_kind':'eq.symptom','mission_id':'eq.DEMO-02','order':'received_at.desc','limit':'20'})
                    found=st==200 and isinstance(rows,list) and any('Synthetic one-go cloud test' in json.dumps(x) for x in rows)
                    log('Dev2 symptom cloud readback','PASS' if found else 'FAIL',f'HTTP {st}; matching tagged symptom found={found}')
    if not args.skip_scenarios:scenario_tests()
    return finish()

def finish():
    out=ROOT/'teamrocket_one_go_result.json'
    # reports may contain synthetic payload or error excerpt but NEVER secrets
    out.write_text(json.dumps({'timestamp':datetime.now(timezone.utc).isoformat(),'checks':RESULTS},indent=2),encoding='utf-8')
    counts={s:sum(x['status']==s for x in RESULTS) for s in ['PASS','FAIL','BLOCKED']}
    print('\n=== RESULTS ===',counts,'\nReport:',out)
    if counts['FAIL'] or counts['BLOCKED']:
        print('NOT YET VERIFIED: resolve failed/blocked checks; do not declare finished')
        return 1
    print('ALL RUN CHECKS PASSED — local API and one cloud sample verified')
    return 0

if __name__=='__main__':sys.exit(main())
