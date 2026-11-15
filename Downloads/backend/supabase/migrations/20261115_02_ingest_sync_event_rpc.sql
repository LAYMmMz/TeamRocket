CREATE EXTENSION IF NOT EXISTS pgcrypto;

DROP TABLE IF EXISTS public.sync_audit_log CASCADE;
DROP TABLE IF EXISTS public.sync_receipts CASCADE;

CREATE TABLE public.sync_receipts (
    receipt_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id TEXT UNIQUE NOT NULL,
    mission_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    record_id TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    previous_hash TEXT,
    immutable BOOLEAN NOT NULL DEFAULT TRUE,
    received_by UUID REFERENCES auth.users(id),
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.sync_audit_log (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id TEXT NOT NULL,
    receipt_id UUID REFERENCES public.sync_receipts(receipt_id),
    mission_id TEXT NOT NULL,
    actor_id UUID,
    action TEXT NOT NULL,
    audit_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.sync_receipts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sync_audit_log ENABLE ROW LEVEL SECURITY;

INSERT INTO public.astronauts (id, crew_code, display_name, status)
VALUES
    ('8c4a271a-863c-4c1f-9a57-62e38b0b2bd9', 'ASTRO-SYNTH-01', 'Synthetic Test Astronaut 01', 'ACTIVE'),
    ('9d5b382b-974d-4d2a-8b68-73f49c1c3ce0', 'TEST-CREW-01', 'Demo Crew Member 01', 'ACTIVE')
ON CONFLICT (id) DO NOTHING;

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
    v_astronaut_raw TEXT := NULLIF(trim(v_payload->>'astronaut_id'), '');
    v_astronaut_id UUID;
    v_log_id UUID;
    v_existing RECORD;
    v_receipt_id UUID;
BEGIN
    IF v_user_id IS NULL THEN
        RAISE EXCEPTION 'Unauthorized: authenticated user JWT required' USING ERRCODE = '28000';
    END IF;

    IF v_event_id IS NULL OR v_kind IS NULL OR v_record_id IS NULL OR v_payload_hash IS NULL OR v_mission_id IS NULL THEN
        RAISE EXCEPTION 'Invalid event: event_id, kind, record_id, payload_hash, and mission_id are required' USING ERRCODE = '22023';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'mission_members') THEN
        IF NOT EXISTS (
            SELECT 1 FROM public.mission_members
            WHERE user_id = v_user_id AND mission_id = v_mission_id
        ) THEN
            RAISE EXCEPTION 'Forbidden: user not authorized for mission %', v_mission_id USING ERRCODE = '42501';
        END IF;
    END IF;

    SELECT receipt_id, payload_hash
    INTO v_existing
    FROM public.sync_receipts
    WHERE event_id = v_event_id;

    IF FOUND THEN
        IF v_existing.payload_hash = v_payload_hash THEN
            RETURN jsonb_build_object(
                'event_id', v_event_id,
                'payload_hash', v_payload_hash,
                'receipt_id', v_existing.receipt_id
            );
        ELSE
            INSERT INTO public.sync_audit_log (event_id, receipt_id, mission_id, actor_id, action, audit_payload)
            VALUES (v_event_id, v_existing.receipt_id, v_mission_id, v_user_id, 'CONFLICT_REJECTED',
                    jsonb_build_object('expected_hash', v_existing.payload_hash, 'received_hash', v_payload_hash));

            RAISE EXCEPTION 'Conflict: event_id % already exists with a different payload_hash', v_event_id
                USING ERRCODE = '23505';
        END IF;
    END IF;

    IF v_astronaut_raw ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' THEN
        v_astronaut_id := v_astronaut_raw::UUID;
    ELSIF v_astronaut_raw IS NOT NULL THEN
        SELECT id INTO v_astronaut_id FROM public.astronauts WHERE crew_code = v_astronaut_raw LIMIT 1;
    END IF;

    IF v_astronaut_id IS NULL THEN
        v_astronaut_id := v_user_id;
    END IF;

    IF v_record_id ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' THEN
        v_log_id := v_record_id::UUID;
    ELSE
        v_log_id := md5(v_kind || ':' || v_record_id)::UUID;
    END IF;

    IF v_kind IN ('measurement', 'vital_sign') THEN
        INSERT INTO public.health_logs (
            id, astronaut_id, mission_id, source_device_id, source_type,
            unit, original_value, original_unit, normalized_value,
            normalized_unit, quality_status, verification_status,
            heart_rate, measured_at, received_at, created_at, audit_context
        )
        VALUES (
            v_log_id,
            v_astronaut_id,
            v_mission_id,
            v_payload->>'source_device_id',
            COALESCE(v_payload->>'source_type', 'SIMULATED'),
            COALESCE(v_payload->>'normalized_unit', v_payload->>'original_unit'),
            (v_payload->>'original_value')::NUMERIC,
            v_payload->>'original_unit',
            (v_payload->>'normalized_value')::NUMERIC,
            v_payload->>'normalized_unit',
            COALESCE(v_payload->>'quality_status', 'Valid'),
            COALESCE(v_payload->>'verification_status', 'Pending'),
            CASE WHEN v_payload->>'metric_code' = 'heart_rate' THEN (v_payload->>'normalized_value')::INTEGER ELSE NULL END,
            (v_payload->>'measured_at')::TIMESTAMPTZ,
            NOW(),
            NOW(),
            v_audit
        )
        ON CONFLICT (id) DO NOTHING;
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
        'event_id', v_event_id,
        'payload_hash', v_payload_hash,
        'receipt_id', v_receipt_id
    );
END;
$$;

REVOKE ALL ON FUNCTION public.ingest_sync_event(JSONB) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.ingest_sync_event(JSONB) TO authenticated;