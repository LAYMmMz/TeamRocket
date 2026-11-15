"""Read-only domain analyses using existing encrypted, authorized Store."""
from fastapi import APIRouter, Depends, HTTPException
from app.auth.dependencies import require
from app.core.dependencies import get_store
from app.domain2.contracts import DOMAIN_FIELDS, PRIVATE_DOMAINS
from app.domain2.router import privacy_gate
from app.domain2.clinical_logic import (active_examination, matched_comparisons,
                                         radiation_summary, environmental_window, review_plan)
router = APIRouter(prefix='/domain2/analysis', tags=['Developer 2 conservative domain analysis'])

@router.get('/examination-schedule')
def examination_schedule(mission_id:str,at:str,principal=Depends(require('measurements:read')),store=Depends(get_store)):
    principal.require_mission(mission_id)
    rows=store.list('dev2_exams',mission_id=mission_id)
    from app.domain2.clinical_logic import moment
    try:moment(at)
    except (ValueError,TypeError):raise HTTPException(422,'Use a timezone-aware --at timestamp')
    return {'items':[{'event_id':r['event_id'],'astronaut_id':r.get('astronaut_id'),'status':active_examination(r,at),'scheduled_at':r['data']['scheduled_at']} for r in rows],
            'generated_results':False}

@router.get('/radiation-dose')
def radiation_dose(mission_id:str,principal=Depends(require('measurements:read')),store=Depends(get_store)):
    principal.require_mission(mission_id)
    return radiation_summary(store.list('dev2_radiation',mission_id=mission_id))

@router.get('/environment-windows')
def environment_windows(mission_id:str,metric_code:str,zone:str,minimum_seconds:int=3600,
                        principal=Depends(require('measurements:read')),store=Depends(get_store)):
    principal.require_mission(mission_id)
    if minimum_seconds <= 0:raise HTTPException(422,'minimum_seconds must be positive')
    return environmental_window(store.list('dev2_environment',mission_id=mission_id),metric_code,zone,minimum_seconds)

MATCH_GROUPS={
    'ocular': ('eye','region','method'),
    'bone': ('anatomical_region','method'),
    'fitness': ('assessment_type','test_method'),
    'vascular': ('side','method'),
    'lab_results': ('sample_id','assay_code','method'),
    'environmental_results': ('sample_id','method'),
}
@router.get('/like-for-like/{domain}')
def comparisons(domain:str,mission_id:str,astronaut_id:str,principal=Depends(require('measurements:read')),store=Depends(get_store)):
    principal.require_mission(mission_id)
    if domain not in MATCH_GROUPS:raise HTTPException(404,'Comparison not defined for this domain')
    rows=[r for r in store.list('dev2_'+domain,mission_id=mission_id) if r.get('astronaut_id')==astronaut_id]
    return {'items':matched_comparisons(rows,group_fields=MATCH_GROUPS[domain]),'status':'descriptive_only',
            'missing_or_incomparable_results_not_fabricated':True}

@router.get('/manual-review/{domain}/{event_id}')
def manual_review(domain:str,event_id:str,mission_id:str,principal=Depends(require('measurements:read')),store=Depends(get_store)):
    principal.require_mission(mission_id)
    if domain not in DOMAIN_FIELDS:raise HTTPException(404,'Unknown domain')
    privacy_gate(domain,principal)
    record=store.get('dev2_'+domain,event_id)
    if record is None or record.get('mission_id')!=mission_id:raise HTTPException(404,'Record not found')
    return review_plan(domain,record)
