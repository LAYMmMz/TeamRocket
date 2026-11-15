CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 1. Ensure base tables exist (safe if already created)
CREATE TABLE IF NOT EXISTS public.astronauts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crew_code TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.health_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    astronaut_id UUID NOT NULL REFERENCES public.astronauts(id),
    mission_id TEXT NOT NULL,
    source_device_id TEXT,
    source_type TEXT NOT NULL DEFAULT 'SIMULATED',
    metric_code TEXT,
    value NUMERIC,
    unit TEXT,
    original_value NUMERIC,
    original_unit TEXT,
    normalized_value NUMERIC,
    normalized_unit TEXT,
    quality_status TEXT NOT NULL DEFAULT 'Valid',
    verification_status TEXT NOT NULL DEFAULT 'Pending',
    heart_rate INTEGER,
    measured_at TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    audit_context JSONB NOT NULL DEFAULT '{}'::jsonb
);

ALTER TABLE public.health_logs
    ADD COLUMN IF NOT EXISTS mission_id TEXT,
    ADD COLUMN IF NOT EXISTS source_device_id TEXT,
    ADD COLUMN IF NOT EXISTS source_type TEXT DEFAULT 'SIMULATED',
    ADD COLUMN IF NOT EXISTS metric_code TEXT,
    ADD COLUMN IF NOT EXISTS value NUMERIC,
    ADD COLUMN IF NOT EXISTS unit TEXT,
    ADD COLUMN IF NOT EXISTS original_value NUMERIC,
    ADD COLUMN IF NOT EXISTS original_unit TEXT,
    ADD COLUMN IF NOT EXISTS normalized_value NUMERIC,
    ADD COLUMN IF NOT EXISTS normalized_unit TEXT,
    ADD COLUMN IF NOT EXISTS quality_status TEXT DEFAULT 'Valid',
    ADD COLUMN IF NOT EXISTS verification_status TEXT DEFAULT 'Pending',
    ADD COLUMN IF NOT EXISTS heart_rate INTEGER,
    ADD COLUMN IF NOT EXISTS measured_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS received_at TIMESTAMPTZ DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS audit_context JSONB DEFAULT '{}'::jsonb;

CREATE INDEX IF NOT EXISTS idx_health_logs_astronaut_metric_time
    ON public.health_logs (astronaut_id, metric_code, measured_at DESC);

CREATE TABLE IF NOT EXISTS public.mission_members (
    mission_id TEXT NOT NULL,
    user_id UUID NOT NULL REFERENCES auth.users(id),
    role TEXT NOT NULL DEFAULT 'crew',
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (mission_id, user_id)
);

CREATE TABLE IF NOT EXISTS public.sync_receipts (
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

ALTER TABLE public.sync_receipts
    ADD COLUMN IF NOT EXISTS mission_id TEXT,
    ADD COLUMN IF NOT EXISTS kind TEXT,
    ADD COLUMN IF NOT EXISTS record_id TEXT,
    ADD COLUMN IF NOT EXISTS payload_hash TEXT,
    ADD COLUMN IF NOT EXISTS previous_hash TEXT,
    ADD COLUMN IF NOT EXISTS immutable BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS received_by UUID REFERENCES auth.users(id),
    ADD COLUMN IF NOT EXISTS received_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE TABLE IF NOT EXISTS public.sync_audit_log (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id TEXT NOT NULL,
    receipt_id UUID REFERENCES public.sync_receipts(receipt_id),
    mission_id TEXT NOT NULL,
    actor_id UUID,
    action TEXT NOT NULL,
    audit_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Enable RLS across ALL 5 tables (blocks direct anon table access)
ALTER TABLE public.astronauts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.health_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mission_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sync_receipts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sync_audit_log ENABLE ROW LEVEL SECURITY;

-- Allow authenticated mission members read-only visibility into their own mission data
DROP POLICY IF EXISTS "mission_members_read_own" ON public.mission_members;
CREATE POLICY "mission_members_read_own"
    ON public.mission_members FOR SELECT
    TO authenticated
    USING (user_id = auth.uid());

DROP POLICY IF EXISTS "astronauts_read_authenticated_members" ON public.astronauts;
CREATE POLICY "astronauts_read_authenticated_members"
    ON public.astronauts FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.mission_members mm
            WHERE mm.user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "health_logs_read_mission_members" ON public.health_logs;
CREATE POLICY "health_logs_read_mission_members"
    ON public.health_logs FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.mission_members mm
            WHERE mm.mission_id = health_logs.mission_id
              AND mm.user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "sync_receipts_read_mission_members" ON public.sync_receipts;
CREATE POLICY "sync_receipts_read_mission_members"
    ON public.sync_receipts FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.mission_members mm
            WHERE mm.mission_id = sync_receipts.mission_id
              AND mm.user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "sync_audit_log_read_mission_members" ON public.sync_audit_log;
CREATE POLICY "sync_audit_log_read_mission_members"
    ON public.sync_audit_log FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.mission_members mm
            WHERE mm.mission_id = sync_audit_log.mission_id
              AND mm.user_id = auth.uid()
        )
    );

-- 3. Seed synthetic astronauts and DEMO-02 mission membership (guarded by auth.users existence)
INSERT INTO public.astronauts (id, crew_code, display_name, status)
VALUES
    ('8c4a271a-863c-4c1f-9a57-62e38b0b2bd9', 'ASTRO-SYNTH-01', 'Synthetic Test Astronaut 01', 'ACTIVE'),
    ('9d5b382b-974d-4d2a-8b68-73f49c1c3ce0', 'TEST-CREW-01', 'Demo Crew Member 01', 'ACTIVE')
ON CONFLICT (id) DO NOTHING;

DO $$
DECLARE
    v_operator_uid UUID;
BEGIN
    SELECT id INTO v_operator_uid
    FROM auth.users
    WHERE id = '7828d6d5-0f32-4634-a810-3680a64b6059'
       OR email = 'operator.demo02@teamrocket.test'
    ORDER BY (id = '7828d6d5-0f32-4634-a810-3680a64b6059') DESC
    LIMIT 1;

    IF v_operator_uid IS NOT NULL THEN
        INSERT INTO public.mission_members (mission_id, user_id, role)
        VALUES ('DEMO-02', v_operator_uid, 'operator')
        ON CONFLICT (mission_id, user_id) DO NOTHING;
    ELSE
        RAISE NOTICE 'Skipping DEMO-02 mission_members seed: create operator.demo02@teamrocket.test in Supabase Auth first.';
    END IF;
END;
$$;

-- 4. RPC Function: stores metric_code + value and rejects duplicate health_logs IDs
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
    v_metric_code TEXT := NULLIF(trim(COALESCE(v_payload->>'metric_code', v_payload->>'metric')), '');
    v_orig_val NUMERIC := COALESCE((v_payload->>'original_value')::NUMERIC, (v_payload->>'value')::NUMERIC);
    v_norm_val NUMERIC := COALESCE((v_payload->>'normalized_value')::NUMERIC, (v_payload->>'value')::NUMERIC);
    v_orig_unit TEXT := NULLIF(trim(COALESCE(v_payload->>'original_unit', v_payload->>'unit')), '');
    v_norm_unit TEXT := NULLIF(trim(COALESCE(v_payload->>'normalized_unit', v_payload->>'unit')), '');
    v_quality TEXT := COALESCE(NULLIF(trim(COALESCE(v_payload->>'quality_status', v_payload->>'quality')), ''), 'Valid');
    v_measured_at TIMESTAMPTZ := COALESCE((v_payload->>'measured_at')::TIMESTAMPTZ, (v_payload->>'timestamp')::TIMESTAMPTZ);

    v_log_id UUID;
    v_inserted_log_id UUID;
    v_existing RECORD;
    v_receipt_id UUID;
BEGIN
    IF v_user_id IS NULL THEN
        RAISE EXCEPTION 'Unauthorized: authenticated user JWT required' USING ERRCODE = '28000';
    END IF;

    IF v_event_id IS NULL OR v_kind IS NULL OR v_record_id IS NULL OR v_payload_hash IS NULL OR v_mission_id IS NULL THEN
        RAISE EXCEPTION 'Invalid event: event_id, kind, record_id, payload_hash, and mission_id are required' USING ERRCODE = '22023';
    END IF;

    IF v_kind NOT IN ('measurement', 'vital_sign') THEN
        RAISE EXCEPTION 'Unsupported event kind: %. Only measurement and vital_sign are currently enabled.', v_kind USING ERRCODE = '22023';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM public.mission_members
        WHERE user_id = v_user_id AND mission_id = v_mission_id
    ) THEN
        RAISE EXCEPTION 'Forbidden: user % is not authorized for mission %', v_user_id, v_mission_id USING ERRCODE = '42501';
    END IF;

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

    IF v_metric_code IS NULL OR v_orig_val IS NULL OR v_orig_unit IS NULL OR v_measured_at IS NULL THEN
        RAISE EXCEPTION 'Invalid measurement payload: metric/metric_code, value/original_value, unit/original_unit, and timestamp/measured_at are required' USING ERRCODE = '22023';
    END IF;

    IF v_record_id ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' THEN
        v_log_id := v_record_id::UUID;
    ELSE
        v_log_id := md5(v_kind || ':' || v_record_id)::UUID;
    END IF;

    INSERT INTO public.health_logs (
        id, astronaut_id, mission_id, source_device_id, source_type,
        metric_code, value, unit, original_value, original_unit,
        normalized_value, normalized_unit, quality_status, verification_status,
        heart_rate, measured_at, received_at, created_at, audit_context
    )
    VALUES (
        v_log_id,
        v_astronaut_id,
        v_mission_id,
        v_payload->>'source_device_id',
        COALESCE(v_payload->>'source_type', 'SIMULATED'),
        v_metric_code,
        v_norm_val,
        v_norm_unit,
        v_orig_val,
        v_orig_unit,
        v_norm_val,
        v_norm_unit,
        v_quality,
        COALESCE(v_payload->>'verification_status', 'Pending'),
        CASE WHEN v_metric_code = 'heart_rate' THEN ROUND(v_norm_val)::INTEGER ELSE NULL END,
        v_measured_at,
        NOW(),
        NOW(),
        v_audit
    )
    ON CONFLICT (id) DO NOTHING
    RETURNING id INTO v_inserted_log_id;

    IF v_inserted_log_id IS NULL THEN
        INSERT INTO public.sync_audit_log (
            event_id, receipt_id, mission_id, actor_id, action, audit_payload
        )
        VALUES (
            v_event_id,
            NULL,
            v_mission_id,
            v_user_id,
            'CONFLICT_REJECTED',
            jsonb_build_object(
                'reason', 'duplicate_health_log_id',
                'record_id', v_record_id,
                'health_log_id', v_log_id
            )
        );

        RETURN jsonb_build_object(
            'status', 'conflict',
            'code', '23505',
            'event_id', v_event_id,
            'record_id', v_record_id,
            'health_log_id', v_log_id,
            'message', 'Conflict: health_logs record id already exists; incoming measurement was not stored'
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
