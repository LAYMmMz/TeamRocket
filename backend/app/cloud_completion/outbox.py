"""Local, transactional clinical outbox for the merged Dev2 SQLAlchemy database.

Clinical records are staged in the SAME database transaction as their source rows.
A separate drain step moves committed events to Dev1's encrypted SQLite queue.
Cloud delivery remains the existing Dev1 SyncWorker's responsibility.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from hashlib import sha256
import json
import logging
import os
from datetime import timezone
import uuid
from sqlalchemy import DateTime, Integer, JSON, String, event, inspect, select
from sqlalchemy.orm import Mapped, Session, mapped_column, sessionmaker
from app.models.dev2_models import Base

log = logging.getLogger(__name__)

# Enumerated from the friend's committed Dev2 SQLAlchemy domain models.
CLINICAL_TABLES = frozenset({
    'vital_signs','ecg_records','health_baselines','symptom_reports',
    'exercise_sessions','mission_locations','radiation_area_records',
    'personal_dose_records','radiation_events','environmental_readings',
    'environmental_samples','environmental_lab_results','gravity_transition_events',
    'functional_assessments','fluid_balance_logs','sleep_sessions',
    'behavioral_checkins','medical_exam_schedule','vascular_ultrasound_results',
    'ocular_assessments','ocular_results','bone_scans','bone_density_results',
    'fitness_assessments','biological_samples','clinical_sample_chain',
    'laboratory_results','sequencing_runs'
})

class ClinicalCloudOutbox(Base):
    __tablename__ = 'teamrocket_clinical_cloud_outbox'
    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    resource_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    mission_id: Mapped[str] = mapped_column(String(120), nullable=False, default='DEMO-01')
    source_id: Mapped[str] = mapped_column(String(160), nullable=False)
    record_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='pending', index=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(String(250), nullable=True)


def _safe_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (uuid.UUID, Decimal)):
        return str(value)
    if isinstance(value, (bytes, bytearray)):
        # No binary/clinical attachments in an event envelope.
        return {'binary_omitted': True, 'bytes': len(value)}
    if isinstance(value, dict):
        return {str(k): _safe_value(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_safe_value(x) for x in value]
    return value


def _snapshot(entity):
    state = inspect(entity)
    payload = {col.key: _safe_value(getattr(entity, col.key))
               for col in state.mapper.column_attrs}
    return payload


def _collect_before_flush(session, _flush_context, _instances):
    if not session.info.get('teamrocket_clinical_outbox_enabled'):
        return
    selected = []
    for entity in list(session.new) + list(session.dirty):
        table = getattr(entity, '__tablename__', '')
        if table not in CLINICAL_TABLES:
            continue
        if entity in session.dirty and not session.is_modified(entity, include_collections=False):
            continue
        selected.append(entity)
    session.info.setdefault('_teamrocket_pending_clinical', []).extend(selected)


def _capture_after_flush(session, _flush_context):
    queued = session.info.pop('_teamrocket_pending_clinical', [])
    if not queued:
        return
    for entity in queued:
        # SQLAlchemy assigns default IDs during flush, before after_flush_postexec.
        resource = entity.__tablename__
        payload = _snapshot(entity)
        pk = inspect(entity).mapper.primary_key
        source_id = ':'.join(str(payload.get(col.key)) for col in pk)
        mission_id = str(payload.get('mission_id') or 'DEMO-01')
        canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
        digest = sha256(canonical.encode('utf-8')).hexdigest()
        deterministic_id = str(uuid.uuid5(uuid.NAMESPACE_URL,
            f'teamrocket:{mission_id}:{resource}:{source_id}:{digest}'))
        if session.get(ClinicalCloudOutbox, deterministic_id) is None:
            session.add(ClinicalCloudOutbox(
                event_id=deterministic_id, resource_type=resource,
                mission_id=mission_id, source_id=source_id,
                record_payload=payload,
                status='pending', attempts=0,
            ))

# Only install listeners once per Python process.
if not getattr(Session, '_teamrocket_clinical_listeners_installed', False):
    event.listen(Session, 'before_flush', _collect_before_flush)
    event.listen(Session, 'after_flush_postexec', _capture_after_flush)
    Session._teamrocket_clinical_listeners_installed = True


def activate(session):
    """Call before routes use their injected clinical SQLAlchemy Session."""
    session.info['teamrocket_clinical_outbox_enabled'] = True


# The Database branch at 65eda22 accepts only these nine RPC event kinds.
# Route Dev2 source tables to a declared cloud kind; retain the source in JSON.
CLINICAL_KIND_BY_TABLE = {
    'vital_signs': 'vital_sign',
    'ecg_records': 'examination', 'health_baselines': 'examination',
    'symptom_reports': 'symptom',
    'exercise_sessions': 'wellness', 'mission_locations': 'environment',
    'radiation_area_records': 'radiation', 'personal_dose_records': 'radiation',
    'radiation_events': 'radiation', 'environmental_readings': 'environment',
    'environmental_samples': 'environment', 'environmental_lab_results': 'laboratory_result',
    'gravity_transition_events': 'wellness', 'functional_assessments': 'examination',
    'fluid_balance_logs': 'wellness', 'sleep_sessions': 'wellness',
    'behavioral_checkins': 'wellness', 'medical_exam_schedule': 'examination',
    'vascular_ultrasound_results': 'examination', 'ocular_assessments': 'examination',
    'ocular_results': 'examination', 'bone_scans': 'examination',
    'bone_density_results': 'examination', 'fitness_assessments': 'examination',
    'biological_samples': 'laboratory_result', 'clinical_sample_chain': 'laboratory_result',
    'laboratory_results': 'laboratory_result', 'sequencing_runs': 'laboratory_result',
}
assert set(CLINICAL_KIND_BY_TABLE) == CLINICAL_TABLES


def _timestamp(raw):
    for key in ('recorded_at', 'measured_at', 'reported_at', 'collected_at',
                'occurred_at', 'onset_at', 'created_at', 'received_at',
                'due_at', 'start_at', 'end_at'):
        value = raw.get(key)
        if value:
            return str(value)
    # Event occurrence time unavailable: set an explicit ingestion time.
    return datetime.now(timezone.utc).isoformat()


def _payload_for_cloud(row):
    raw = row.record_payload
    kind = CLINICAL_KIND_BY_TABLE.get(row.resource_type)
    if not kind:
        raise ValueError('Unmapped clinical table: ' + row.resource_type)
    # Environmental/area records do not always identify an astronaut. A demo
    # fallback must be explicitly configured; never silently fabricate identity.
    astronaut = raw.get('astronaut_id') or raw.get('crew_code')
    if not astronaut:
        astronaut = os.getenv('SYNC_DEFAULT_ASTRONAUT_CODE', '').strip()
    if not astronaut:
        raise ValueError('Missing astronaut_id; set SYNC_DEFAULT_ASTRONAUT_CODE for synthetic area/shared records only')
    timestamp = _timestamp(raw)
    payload = {
        'astronaut_id': str(astronaut),
        'recorded_at': timestamp,
        'source_type': str(raw.get('source_type') or 'DEV2_LOCAL'),
        'source_device_id': raw.get('source_device_id'),
        'title': str(raw.get('title') or raw.get('exam_type') or raw.get('test_code') or row.resource_type),
        'status': str(raw.get('status') or 'recorded'),
        'resource_type': row.resource_type,
        'source_id': row.source_id,
        'record': raw,
    }
    if kind == 'vital_sign':
        metric = raw.get('metric_code') or raw.get('metric')
        value = raw.get('normalized_value')
        if value is None:
            value = raw.get('raw_value')
        if value is None:
            value = raw.get('value')
        unit = raw.get('normalized_unit') or raw.get('raw_unit') or raw.get('unit')
        if metric is None or value is None or not unit:
            raise ValueError('Vital sign requires metric_code, numeric value and unit')
        payload.update({
            'metric_code': str(metric), 'value': value, 'unit': str(unit),
            'timestamp': timestamp,
            'original_value': raw.get('raw_value') if raw.get('raw_value') is not None else value,
            'original_unit': str(raw.get('raw_unit') or unit),
        })
    return kind, payload


def drain(store, session_factory: sessionmaker, *, limit=200):
    """Stage committed clinical changes into Dev1's encrypted queue.

    'enqueued' means local queue accepted the event, NOT cloud delivery.
    A failed mapping remains pending and is never counted as synced.
    """
    if store is None:
        return {'enqueued': 0, 'pending': 0, 'error': 'Dev1 store not ready'}
    enqueued = 0
    with session_factory() as session:
        rows = session.scalars(select(ClinicalCloudOutbox)
            .where(ClinicalCloudOutbox.status == 'pending')
            .order_by(ClinicalCloudOutbox.event_id).limit(limit)).all()
        for row in rows:
            event_id = row.event_id
            try:
                kind, payload = _payload_for_cloud(row)
                store.put(kind, event_id, payload,
                    mission_id=row.mission_id, actor_id='dev2-clinical-outbox',
                    immutable=True, enqueue=True, priority=20)
                row.status = 'enqueued'
                row.last_error = None
                session.commit()
                enqueued += 1
            except Exception as exc:
                session.rollback()
                log.warning('Clinical outbox staging failed (%s): %s',
                            row.resource_type, type(exc).__name__)
                with session_factory.begin() as retry_session:
                    item = retry_session.get(ClinicalCloudOutbox, event_id)
                    if item is not None:
                        item.attempts += 1
                        item.last_error = str(exc)[:250]
        pending = session.scalar(select(__import__('sqlalchemy').func.count())
            .select_from(ClinicalCloudOutbox)
            .where(ClinicalCloudOutbox.status == 'pending'))
    return {'enqueued': enqueued, 'pending': int(pending or 0)}
