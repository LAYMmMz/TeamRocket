-- TeamRocket add-on migration. Run ONLY on reviewed/test Supabase project first.
-- Does NOT alter existing measurement/vital_sign RPC or protected local SQLite.
-- Generic, access-controlled clinical evidence staging (NOT normalized 57-table mapping).
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS public.clinical_sync_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id TEXT NOT NULL UNIQUE,
  mission_id TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  source_id TEXT NOT NULL,
  payload_hash TEXT NOT NULL,
  record JSONB NOT NULL,
  submitted_by UUID NOT NULL REFERENCES auth.users(id),
  received_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS clinical_sync_records_mission_type_idx
  ON public.clinical_sync_records(mission_id, resource_type, received_at DESC);
ALTER TABLE public.clinical_sync_records ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.clinical_sync_records FROM anon;
REVOKE INSERT, UPDATE, DELETE ON public.clinical_sync_records FROM authenticated;
GRANT SELECT ON public.clinical_sync_records TO authenticated;
DROP POLICY IF EXISTS clinical_sync_records_read_mission ON public.clinical_sync_records;
CREATE POLICY clinical_sync_records_read_mission ON public.clinical_sync_records
FOR SELECT TO authenticated
USING (EXISTS (SELECT 1 FROM public.mission_members mm
              WHERE mm.mission_id = clinical_sync_records.mission_id
                AND mm.user_id = (SELECT auth.uid())
                AND (
                  clinical_sync_records.resource_type NOT IN (
                    'behavioral_checkins', 'symptom_reports', 'laboratory_results',
                    'biological_samples', 'clinical_sample_chain', 'sequencing_runs',
                    'medical_exam_schedule', 'vascular_ultrasound_results',
                    'ocular_assessments', 'ocular_results', 'bone_scans',
                    'bone_density_results'
                  ) OR lower(mm.role) IN ('flight_surgeon','medical_officer','admin')
                )));

CREATE OR REPLACE FUNCTION public.ingest_clinical_sync_event(p_event JSONB)
RETURNS JSONB
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp
AS $$
DECLARE
  ev TEXT := NULLIF(trim(p_event->>'event_id'), '');
  rec_id TEXT := NULLIF(trim(p_event->>'record_id'), '');
  mid TEXT := NULLIF(trim(p_event->>'mission_id'), '');
  digest TEXT := NULLIF(trim(p_event->>'payload_hash'), '');
  p JSONB := p_event->'payload';
  kind TEXT := p_event->>'kind';
  domain TEXT := NULLIF(trim(p->>'resource_type'), '');
  doc JSONB := p->'record';
  uid UUID := auth.uid();
  previous RECORD;
  new_id UUID;
BEGIN
  IF uid IS NULL THEN
    RAISE EXCEPTION 'Authenticated JWT required' USING ERRCODE = '28000';
  END IF;
  IF kind IS DISTINCT FROM 'clinical_record'
      OR ev IS NULL OR rec_id IS NULL OR mid IS NULL OR digest IS NULL
      OR p IS NULL OR jsonb_typeof(p) <> 'object'
      OR doc IS NULL OR jsonb_typeof(doc) <> 'object'
      OR domain IS NULL OR NULLIF(trim(p->>'source_id'),'') IS NULL THEN
    RAISE EXCEPTION 'Invalid clinical event contract' USING ERRCODE = '22023';
  END IF;
  IF p->>'mission_id' IS DISTINCT FROM mid THEN
    RAISE EXCEPTION 'Mission ID mismatch' USING ERRCODE = '22023';
  END IF;
  IF domain NOT IN (
    'vital_signs','ecg_records','health_baselines','symptom_reports',
    'exercise_sessions','mission_locations','radiation_area_records',
    'personal_dose_records','radiation_events','environmental_readings',
    'environmental_samples','environmental_lab_results','gravity_transition_events',
    'functional_assessments','fluid_balance_logs','sleep_sessions',
    'behavioral_checkins','medical_exam_schedule','vascular_ultrasound_results',
    'ocular_assessments','ocular_results','bone_scans','bone_density_results',
    'fitness_assessments','biological_samples','clinical_sample_chain',
    'laboratory_results','sequencing_runs'
  ) THEN
    RAISE EXCEPTION 'Unsupported clinical resource type' USING ERRCODE = '22023';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM public.mission_members mm
                 WHERE mm.mission_id = mid AND mm.user_id = uid) THEN
    RAISE EXCEPTION 'Mission membership required' USING ERRCODE = '42501';
  END IF;
  SELECT id, payload_hash INTO previous FROM public.clinical_sync_records
   WHERE event_id = ev;
  IF FOUND THEN
    IF previous.payload_hash = digest THEN
      RETURN jsonb_build_object('status','duplicate_ok','event_id',ev,
        'payload_hash',digest,'receipt_id',previous.id);
    END IF;
    -- Audited in durable sync_audit_log; do not RAISE after INSERT (transaction rollback).
    INSERT INTO public.sync_audit_log(event_id, mission_id, actor_id, action, audit_payload)
    VALUES(ev, mid, uid, 'CONFLICT_REJECTED',
      jsonb_build_object('previous_hash', previous.payload_hash, 'incoming_hash', digest));
    RETURN jsonb_build_object('status','conflict','event_id',ev,
      'payload_hash',digest,'receipt_id',previous.id,'code','23505');
  END IF;
  INSERT INTO public.clinical_sync_records
      (event_id,mission_id,resource_type,source_id,payload_hash,record,submitted_by)
  VALUES(ev,mid,domain,p->>'source_id',digest,doc,uid)
  RETURNING id INTO new_id;
  INSERT INTO public.sync_audit_log(event_id,mission_id,actor_id,action,audit_payload)
  VALUES(ev,mid,uid,'CLINICAL_INGESTED',
    jsonb_build_object('resource_type', domain, 'source_id', p->>'source_id'));
  RETURN jsonb_build_object('status','ingested','event_id',ev,
      'payload_hash',digest,'receipt_id',new_id);
END;
$$;
REVOKE ALL ON FUNCTION public.ingest_clinical_sync_event(JSONB) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.ingest_clinical_sync_event(JSONB) TO authenticated;
