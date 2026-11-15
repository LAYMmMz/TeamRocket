"""Seven API-level mission dashboard summaries, with role-gated private data.

These are descriptive JSON/CSV views of local stored evidence, NOT diagnoses.
"""
import csv
import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from app.auth.dependencies import require
from app.core.dependencies import get_store
from app.domain2.contracts import PRIVATE_DOMAINS

router=APIRouter(prefix='/reports',tags=['Developer 2 seven-dashboard reports'])
DASHBOARD_DOMAINS={
    'flight-health': ['baselines','symptoms','exams','vascular','ocular','bone','fitness'],
    'vital-signs': ['_measurement','ecg','exercise','sleep'],
    'radiation': ['radiation','dose_events'],
    'environment': ['environment','habitat_events','environmental_samples','environmental_results'],
    'wellness': ['sleep','nutrition','exercise','behavioral','hydration'],
    'laboratory': ['samples','lab_results','sequencing','vascular','ocular'],
    'medical-operations': ['_health_alert','_incident','_symptom_report','exams','symptoms','vascular','bone'],
}

def authorized(domain,principal):
    return domain not in PRIVATE_DOMAINS or bool(set(principal.roles).intersection({'admin','flight_surgeon'}))

def rows_for(dashboard,mission_id,principal,store):
    if dashboard not in DASHBOARD_DOMAINS:raise HTTPException(404,'Unknown dashboard')
    results=[]
    for domain in DASHBOARD_DOMAINS[dashboard]:
        if not authorized(domain,principal):continue
        rows=store.list(domain[1:] if domain.startswith('_') else 'dev2_'+domain,mission_id=mission_id)
        for row in rows:
            results.append({
                'domain':domain.lstrip('_'),'event_id':row.get('event_id') or row.get('incident_id') or row.get('id'),
                'astronaut_id':row.get('astronaut_id'),
                'measured_at':row.get('measured_at') or row.get('recorded_at') or '',
                'received_at':row.get('received_at') or '',
                'source_type':row.get('source_type','UNAVAILABLE'),'is_synthetic':row.get('is_synthetic'),
                'quality':row.get('quality','UNAVAILABLE'),'verification':row.get('verification','UNAVAILABLE'),
                'review_status':(row.get('data') or {}).get('review_status','NOT_REVIEWED'),
            })
    return sorted(results,key=lambda r:(r['measured_at'],r['domain'],str(r['event_id'])))

@router.get('/dashboards')
def list_dashboards(principal=Depends(require('foundation:read'))):
    return {'dashboards':list(DASHBOARD_DOMAINS),'format':['json','csv'],
            'source':'local_encrypted_store','clinical_interpretation':False}

@router.get('/dashboards/{dashboard}')
def dashboard_report(dashboard:str,mission_id:str,format:str='json',
                     principal=Depends(require('foundation:read')),store=Depends(get_store)):
    principal.require_mission(mission_id)
    if format not in ('json','csv'):raise HTTPException(422,'format must be json or csv')
    rows=rows_for(dashboard,mission_id,principal,store)
    if format=='json':
        return {'dashboard':dashboard,'mission_id':mission_id,'items':rows,
                'record_count':len(rows),'is_clinical_advice':False,
                'private_domains_excluded':not authorized('behavioral',principal)}
    fields=['domain','event_id','astronaut_id','measured_at','received_at','source_type','is_synthetic','quality','verification','review_status']
    out=io.StringIO(newline='');w=csv.DictWriter(out,fieldnames=fields,lineterminator='\r\n');w.writeheader()
    # Prevent spreadsheet formula injection through user-provided identifier strings.
    def safe(x):
        if isinstance(x,str) and x.lstrip().startswith(('=','+','-','@')):return "'"+x
        return x
    for row in rows:w.writerow({k:safe(row.get(k,'')) for k in fields})
    return Response(content=out.getvalue(),media_type='text/csv',headers={'Content-Disposition':f'attachment; filename="{dashboard}-report.csv"'})
