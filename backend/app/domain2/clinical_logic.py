"""Conservative, source-safe descriptive computations for Dev 2 domains.

No medical thresholds, diagnosis, EVA clearance, treatment, or prescription.
"""
from __future__ import annotations
from datetime import datetime, timezone
from collections import defaultdict
import math


def moment(value):
    if isinstance(value, datetime):
        out = value
    else:
        out = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    if out.tzinfo is None:
        raise ValueError('timezone-aware timestamp required')
    return out.astimezone(timezone.utc)


def active_examination(record, at):
    """Scheduling projection; never invent test results."""
    d = record['data']
    status = d['status']
    if status in {'CANCELLED', 'COMPLETED'}:
        return status
    due = moment(d['scheduled_at'])
    return 'OVERDUE' if due < moment(at) else 'DUE' if due == moment(at) else 'PLANNED'


def only_verified(records):
    return [r for r in records if r.get('quality') == 'VALID' and r.get('verification') == 'VERIFIED']


def matched_comparisons(records, *, group_fields, value_field='original_value', unit_field='original_unit'):
    """Group by assay, eye, region, method, units, etc. Never mix groups."""
    groups = defaultdict(list)
    for row in only_verified(records):
        d = row.get('data') or {}
        key = tuple(d.get(k) for k in group_fields) + (d.get(unit_field),)
        val = d.get(value_field)
        if any(v is None for v in key) or not isinstance(val, (float, int)) or isinstance(val, bool) or not math.isfinite(val):
            continue
        groups[key].append((moment(row['measured_at']), row['event_id'], float(val)))
    out = []
    for key, group in groups.items():
        group.sort(key=lambda v: (v[0], v[1]))
        if len(group) < 2:
            continue
        a, b = group[0], group[-1]
        out.append({'comparison': dict(zip((*group_fields, unit_field), key)),
                    'earliest_event_id': a[1], 'latest_event_id': b[1],
                    'difference': round(b[2]-a[2], 9), 'count': len(group),
                    'status': 'descriptive_only', 'clinical_interpretation': False})
    return sorted(out, key=lambda x: tuple(str(v) for v in x['comparison'].values()))


def radiation_summary(records):
    """Sum only nonoverlapping, compatible absorbed/effective/equivalent intervals.

    Never converts Gy to Sv; never sums rates or unverified readings.
    """
    valid = only_verified(records)
    by_key = defaultdict(list)
    rejected = []
    for r in valid:
        d = r.get('data', {})
        q, u = d.get('dose_quantity'), d.get('original_unit')
        if (q,u) not in {('effective','Sv'), ('effective','mSv'), ('effective','uSv'),
                         ('equivalent','Sv'), ('equivalent','mSv'), ('equivalent','uSv'),
                         ('absorbed','Gy'), ('absorbed','mGy')}:
            rejected.append({'event_id':r['event_id'], 'reason':'incompatible_dose_quantity_or_unit'});continue
        try:
            lo, hi = moment(d['interval_start']), moment(d['interval_end'])
            val = d['original_value']
            if lo >= hi or not isinstance(val, (float,int)) or isinstance(val,bool) or not math.isfinite(val) or val < 0:
                raise ValueError('invalid interval/value')
        except (KeyError, ValueError, TypeError):
            rejected.append({'event_id':r['event_id'], 'reason':'invalid_interval_or_value'});continue
        by_key[(r.get('astronaut_id'),q,u,d.get('particle_type'))].append((lo,hi,float(val),r['event_id']))
    totals = []
    for key, items in by_key.items():
        items.sort(key=lambda x:(x[0],x[1]))
        accepted=[];end=None
        for lo,hi,value,eid in items:
            if end is not None and lo < end:
                rejected.append({'event_id':eid,'reason':'overlapping_interval'});continue
            accepted.append((value,eid));end=hi
        totals.append({'astronaut_id':key[0],'dose_quantity':key[1],'unit':key[2],
                       'particle_type':key[3], 'total':round(sum(x[0] for x in accepted),10),
                       'count':len(accepted),'status':'descriptive_only','clinical_interpretation':False})
    return {'totals':totals, 'excluded':rejected, 'note':'No inferred shielding factors or dose-equivalence conversions'}


def environmental_window(records, metric, zone, minimum_seconds=3600):
    """Return evidence windows, not operational CO2 alarm thresholds."""
    good = []
    for r in only_verified(records):
        d = r.get('data') or {}
        if d.get('metric_code') != metric or d.get('zone') != zone:continue
        secs = d.get('averaging_window_seconds')
        val = d.get('original_value')
        if (not isinstance(secs,(int,float)) or isinstance(secs,bool) or secs < minimum_seconds
            or not isinstance(val,(int,float)) or isinstance(val,bool) or not math.isfinite(val)):
            continue
        good.append({'event_id':r['event_id'],'measured_at':r['measured_at'],
                     'value':val,'unit':d['original_unit'],'averaging_window_seconds':secs,
                     'calibration_revision':d['calibration_revision']})
    return {'status':'descriptive_only' if good else 'unavailable', 'windows':good,
            'operational_alarm':False, 'requires_approved_rule':True}


def review_plan(domain, record):
    """Conservative workflow requiring human review; no made-up findings."""
    d=record['data']; reasons=[]; actions=[]
    if domain=='vascular':
        reasons.append('side_specific_ultrasound_or_laboratory_result')
        actions.append('clinician_review')
    elif domain=='lab_results':
        reasons.append('assay_and_sample_context_required')
        actions.append('clinician_review')
    elif domain=='sequencing':
        reasons.append('sequencing_qc_not_diagnostic')
        actions.append('manual_sequence_qc_and_reviewer_signoff')
    elif domain=='environmental_samples':
        reasons.append('interpretation_requires_sampling_method_and_denominator')
        actions.append('sampling_method_review')
        if d.get('flagged') is True:
            actions.append('request_repeat_sampling')
    elif domain=='ocular':
        reasons.append('eye_region_method_matched_review')
        actions.append('clinician_review')
    elif domain=='bone':
        reasons.append('same_anatomical_region_pre_post_only')
        actions.append('clinician_review')
    elif domain=='gravity':
        reasons.append('gravity_transition_requires_assessment')
        actions.append('human_eva_clearance_review')
    elif domain=='symptoms':
        reasons.append('symptom_report_requires_human_review')
        actions.append('medical_review')
    elif domain=='dose_events':
        reasons.append('spe_context_and_dosimeter_freshness_review')
        actions.append('mission_medical_review')
    return {'event_id':record['event_id'], 'status':'REVIEW_REQUIRED' if actions else 'RECORDED',
            'reasons':reasons,'suggested_manual_actions':actions,
            'medical_diagnosis':False, 'eva_clearance_granted':False,
            'operational_alarm':False}
