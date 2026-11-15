"""Unit/method-aware descriptive baseline comparison. No health risk threshold."""
from fastapi import APIRouter,Depends
from app.auth.dependencies import require
from app.core.dependencies import get_store
router=APIRouter(prefix='/baselines', tags=['Developer 2 baseline and trend review'])

@router.get('/compare')
def compare(mission_id:str,astronaut_id:str,metric_code:str,method:str,
            principal=Depends(require('measurements:read')),store=Depends(get_store)):
    principal.require_mission(mission_id)
    baselines=[v for v in store.list('dev2_baselines',mission_id=mission_id)
               if v.get('astronaut_id')==astronaut_id and v.get('data',{}).get('metric_code')==metric_code
               and v.get('data',{}).get('measurement_method')==method and v.get('quality')=='VALID']
    readings=[v for v in store.list('measurement',mission_id=mission_id)
              if v.get('astronaut_id')==astronaut_id and v.get('metric')==metric_code
              and v.get('quality')=='VALID']
    if not baselines or not readings:
        return {'status':'unavailable','reason':'no_matching_valid_baseline_or_measurement','clinical_interpretation':False}
    # Latest record based on supplied measurement time, not arrival order.
    base=max(baselines,key=lambda v:(v['measured_at'],v['event_id']))
    data=base['data'];unit=data.get('unit');baseline=data.get('baseline_value')
    if not isinstance(baseline,(int,float)) or isinstance(baseline,bool) or unit is None:
        return {'status':'unavailable','reason':'baseline_missing_number_or_unit','clinical_interpretation':False}
    comparable=[]
    for row in readings:
        v=row.get('normalized_value')
        u=row.get('normalized_unit')
        if v is None:
            v=row.get('value');u=row.get('unit')
        metadata=row.get('metadata') or {}
        # Prevent comparing exercise HR to resting baseline without method context.
        if metadata.get('measurement_method') != method:
            continue
        if unit!=u or not isinstance(v,(int,float)) or isinstance(v,bool):
            continue
        # All inputs must share verification class or be clearly labeled DEMO.
        synthetic=base.get('is_synthetic') is True and row.get('is_synthetic') is True
        verified=base.get('verification')=='VERIFIED' and row.get('verification')=='VERIFIED'
        if not (verified or synthetic):continue
        comparable.append((row,float(v),verified))
    if not comparable:
        return {'status':'unavailable','reason':'no_like_for_like_unit_method_and_source_evidence',
                'clinical_interpretation':False}
    latest,value,verified=max(comparable,key=lambda e:(e[0]['measured_at'],e[0]['event_id']))
    return {'status':'descriptive_only','difference':round(value-float(baseline),9),'unit':unit,
            'method':method,'baseline_event_id':base['event_id'],
            'measurement_event_id':latest['event_id'], 'source_label':'VERIFIED' if verified else 'SIMULATED_UNVERIFIED',
            'clinical_interpretation':False,'recalculates_on_next_read':True}
