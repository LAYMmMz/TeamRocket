-- 1. Destination table for Dev 2 clinical records (radiation, environment, symptom, laboratory_result, examination, wellness, report)
CREATE TABLE IF NOT EXISTS public.clinical_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    astronaut_id UUID NOT NULL REFERENCES public.astronauts(id),
    mission_id TEXT NOT NULL,
    record_kind TEXT NOT NULL,
    source_device_id TEXT,
    source_type TEXT NOT NULL DEFAULT 'SIMULATED',
    title TEXT,
    status TEXT NOT NULL DEFAULT 'recorded',
    clinical_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    recorded_at TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    audit_context JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_clinical_records_astronaut_kind_time
    ON public.clinical_records (astronaut_id, record_kind, recorded_at DESC);

-- 2. Permissions & RLS (blocks anon reads; allows authenticated mission members only)
ALTER TABLE public.clinical_records ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "clinical_records_read_mission_members" ON public.clinical_records;
CREATE POLICY "clinical_records_read_mission_members"
    ON public.clinical_records FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.mission_members mm
            WHERE mm.mission_id = clinical_records.mission_id
              AND mm.user_id = auth.uid()
        )
    );

-- 3. Expand ingest_sync_event RPC to handle BOTH Dev 1 vitals and Dev 2 clinical records
CREATE OR REPLACE FUNCTION public.ingest_sync_event(p_event JSONB)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_event_id TEXT := NULLIF(trim(p_event->>'event_id'), '');
    v_kind TEXT := NULLIF(trim(p_event->>'kind'), '');
    v_record_id TEXT := NULLIF(trim(p_event->>'record_id'), '');
    v_payload_hash TEXT := NULLIF(trim(p_event->>'payload_hash'), '');
    v_mission_id TEXT := NULLIF(trim(p_event->>'mission_id'), '');
    v_payload JSONB := p_event->'payload';
    v_audit JSONB := COALESCE(p_event->'audit_event', '{}'::jsonb);
    v_immutable BOOLEAN := COALESCE((p_event->>'immutable')::BOOLEAN, TRUE);
    v_previous_hash TEXT := p_event->>'previous_hash';
    v_user_id UUID := auth.uid();

    v_astronaut_raw TEXT := NULLIF(trim(COALESCE(v_payload->>'astronaut_id', v_payload->>'crew_code')), '');
    v_astronaut_id UUID;

    -- Dev 1 vital fields
    v_metric_code TEXT := NULLIF(trim(COALESCE(v_payload->>'metric_code', v_payload->>'metric')), '');
    v_orig_val NUMERIC := COALESCE((v_payload->>'original_value')::NUMERIC, (v_payload->>'value')::NUMERIC);
    v_norm_val NUMERIC := COALESCE((v_payload->>'normalized_value')::NUMERIC, (v_payload->>'value')::NUMERIC);
    v_orig_unit TEXT := NULLIF(trim(COALESCE(v_payload->>'original_unit', v_payload->>'unit')), '');
    v_norm_unit TEXT := NULLIF(trim(COALESCE(v_payload->>'normalized_unit', v_payload->>'unit')), '');
    v_quality TEXT := COALESCE(NULLIF(trim(COALESCE(v_payload->>'quality_status', v_payload->>'quality')), ''), 'Valid');
    v_measured_at TIMESTAMPTZ := COALESCE((v_payload->>'measured_at')::TIMESTAMPTZ, (v_payload->>'timestamp')::TIMESTAMPTZ);

    -- Dev 2 clinical fields
    v_recorded_at TIMESTAMPTZ := COALESCE((v_payload->>'recorded_at')::TIMESTAMPTZ, (v_payload->>'measured_at')::TIMESTAMPTZ, (v_payload->>'timestamp')::TIMESTAMPTZ);
    v_title TEXT := NULLIF(trim(COALESCE(v_payload->>'title', v_payload->>'summary', v_payload->>'exam_type', v_payload->>'test_name')), '');
    v_clinical_status TEXT := COALESCE(NULLIF(trim(v_payload->>'status'), ''), 'recorded');

    v_target_id UUID;
    v_inserted_id UUID;
    v_existing RECORD;
    v_receipt_id UUID;
BEGIN
    IF v_user_id IS NULL THEN
        RAISE EXCEPTION 'Unauthorized: authenticated user JWT required' USING ERRCODE = '28000';
    END IF;

    IF v_event_id IS NULL OR v_kind IS NULL OR v_record_id IS NULL OR v_payload_hash IS NULL OR v_mission_id IS NULL THEN
        RAISE EXCEPTION 'Invalid event: event_id, kind, record_id, payload_hash, and mission_id are required' USING ERRCODE = '22023';
    END IF;

    IF v_kind NOT IN (
        'measurement', 'vital_sign',
        'radiation', 'environment', 'symptom', 'laboratory_result', 'examination', 'wellness', 'report'
    ) THEN
        RAISE EXCEPTION 'Unsupported event kind: %', v_kind USING ERRCODE = '22023';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM public.mission_members
        WHERE user_id = v_user_id AND mission_id = v_mission_id
    ) THEN
        RAISE EXCEPTION 'Forbidden: user % is not authorized for mission %', v_user_id, v_mission_id USING ERRCODE = '42501';
    END IF;

    -- Idempotency & payload_hash conflict check
    SELECT receipt_id, payload_hash
    INTO v_existing
    FROM public.sync_receipts
    WHERE event_id = v_event_id;

    IF FOUND THEN
        IF v_existing.payload_hash = v_payload_hash THEN
            RETURN jsonb_build_object(
                'status', 'duplicate_ok',
                'event_id', v_event_id,
                'payload_hash', v_payload_hash,
                'receipt_id', v_existing.receipt_id
            );
        ELSE
            INSERT INTO public.sync_audit_log (event_id, receipt_id, mission_id, actor_id, action, audit_payload)
            VALUES (
                v_event_id,
                v_existing.receipt_id,
                v_mission_id,
                v_user_id,
                'CONFLICT_REJECTED',
                jsonb_build_object('expected_hash', v_existing.payload_hash, 'received_hash', v_payload_hash)
            );

            RETURN jsonb_build_object(
                'status', 'conflict',
                'code', '23505',
                'event_id', v_event_id,
                'expected_hash', v_existing.payload_hash,
                'received_hash', v_payload_hash,
                'receipt_id', v_existing.receipt_id,
                'message', 'Conflict: event_id already exists with a different payload_hash; immutable record preserved'
            );
        END IF;
    END IF;

    -- Resolve astronaut_id from UUID or crew_code
    IF v_astronaut_raw IS NULL THEN
        RAISE EXCEPTION 'Invalid payload: astronaut_id or crew_code is required' USING ERRCODE = '22023';
    END IF;

    IF v_astronaut_raw ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' THEN
        SELECT id INTO v_astronaut_id FROM public.astronauts WHERE id = v_astronaut_raw::UUID LIMIT 1;
    ELSE
        SELECT id INTO v_astronaut_id FROM public.astronauts WHERE crew_code = v_astronaut_raw LIMIT 1;
    END IF;

    IF v_astronaut_id IS NULL THEN
        RAISE EXCEPTION 'Invalid payload: unknown astronaut identifier %', v_astronaut_raw USING ERRCODE = '22023';
    END IF;

    IF v_record_id ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' THEN
        v_target_id := v_record_id::UUID;
    ELSE
        v_target_id := md5(v_kind || ':' || v_record_id)::UUID;
    END IF;

    -- Branch A: Dev 1 Measurements & Vitals -> public.health_logs
    IF v_kind IN ('measurement', 'vital_sign') THEN
        IF v_metric_code IS NULL OR v_orig_val IS NULL OR v_orig_unit IS NULL OR v_measured_at IS NULL THEN
            RAISE EXCEPTION 'Invalid measurement payload: metric/metric_code, value/original_value, unit/original_unit, and timestamp/measured_at are required' USING ERRCODE = '22023';
        END IF;

        INSERT INTO public.health_logs (
            id, astronaut_id, mission_id, source_device_id, source_type,
            metric_code, value, unit, original_value, original_unit,
            normalized_value, normalized_unit, quality_status, verification_status,
            heart_rate, measured_at, received_at, created_at, audit_context
        )
        VALUES (
            v_target_id, v_astronaut_id, v_mission_id, v_payload->>'source_device_id',
            COALESCE(v_payload->>'source_type', 'SIMULATED'),
            v_metric_code, v_norm_val, v_norm_unit, v_orig_val, v_orig_unit,
            v_norm_val, v_norm_unit, v_quality,
            COALESCE(v_payload->>'verification_status', 'Pending'),
            CASE WHEN v_metric_code = 'heart_rate' THEN ROUND(v_norm_val)::INTEGER ELSE NULL END,
            v_measured_at, NOW(), NOW(), v_audit
        )
        ON CONFLICT (id) DO NOTHING
        RETURNING id INTO v_inserted_id;

    -- Branch B: Dev 2 Clinical Records -> public.clinical_records
    ELSE
        IF v_recorded_at IS NULL THEN
            RAISE EXCEPTION 'Invalid clinical payload: recorded_at or timestamp is required for kind %', v_kind USING ERRCODE = '22023';
        END IF;

        INSERT INTO public.clinical_records (
            id, astronaut_id, mission_id, record_kind, source_device_id, source_type,
            title, status, clinical_payload, recorded_at, received_at, created_at, audit_context
        )
        VALUES (
            v_target_id, v_astronaut_id, v_mission_id, v_kind, v_payload->>'source_device_id',
            COALESCE(v_payload->>'source_type', 'SIMULATED'),
            v_title, v_clinical_status, COALESCE(v_payload, '{}'::jsonb),
            v_recorded_at, NOW(), NOW(), v_audit
        )
        ON CONFLICT (id) DO NOTHING
        RETURNING id INTO v_inserted_id;
    END IF;

    IF v_inserted_id IS NULL THEN
        INSERT INTO public.sync_audit_log (event_id, receipt_id, mission_id, actor_id, action, audit_payload)
        VALUES (
            v_event_id, NULL, v_mission_id, v_user_id, 'CONFLICT_REJECTED',
            jsonb_build_object('reason', 'duplicate_target_record_id', 'kind', v_kind, 'target_id', v_target_id, 'record_id', v_record_id)
        );

        RETURN jsonb_build_object(
            'status', 'conflict',
            'code', '23505',
            'event_id', v_event_id,
            'record_id', v_record_id,
            'message', 'Conflict: target record id already exists; incoming record was not stored'
        );
    END IF;

    INSERT INTO public.sync_receipts (
        event_id, mission_id, kind, record_id, payload_hash, previous_hash, immutable, received_by
    )
    VALUES (
        v_event_id, v_mission_id, v_kind, v_record_id, v_payload_hash, v_previous_hash, v_immutable, v_user_id
    )
    RETURNING receipt_id INTO v_receipt_id;

    INSERT INTO public.sync_audit_log (
        event_id, receipt_id, mission_id, actor_id, action, audit_payload
    )
    VALUES (
        v_event_id, v_receipt_id, v_mission_id, v_user_id, 'INGESTED', v_audit
    );

    RETURN jsonb_build_object(
        'status', 'ingested',
        'event_id', v_event_id,
        'payload_hash', v_payload_hash,
        'receipt_id', v_receipt_id
    );
END;
$$;

REVOKE ALL ON FUNCTION public.ingest_sync_event(JSONB) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.ingest_sync_event(JSONB) TO authenticated;