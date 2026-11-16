-- RocketPulse: PUBLIC synthetic-only telemetry feed.
-- REVIEW BEFORE RUNNING in TeamRocketV2Database (project ziecxjoeljxoocixejtz).
-- This creates ONE new, isolated table and synthetic seed rows. It never reads,
-- copies, changes, or grants anonymous access to clinical tables, health_logs,
-- astronauts, mission_members, or the privileged ingest_sync_event RPC.
-- Existing mission RLS and user authentication stay unchanged.
--
-- Anonymous users get SELECT only on explicitly approved, SIMULATED DEMO-01
-- rows. Nobody gets anonymous insert/update/delete. Do not add free-text
-- patient notes, identifiers, authentication details, or user-provided JSON.

BEGIN;
CREATE TABLE IF NOT EXISTS public.rocketpulse_public_demo_samples (
    event_id text PRIMARY KEY
        CHECK (event_id ~ '^RP-PUBLIC-[A-Z0-9_-]{3,80}$'),
    mission_id text NOT NULL DEFAULT 'DEMO-01'
        CHECK (mission_id = 'DEMO-01'),
    astronaut_code text NOT NULL
        CHECK (astronaut_code IN ('CREW-01','CREW-02','CREW-03','CREW-04')),
    domain text NOT NULL
        CHECK (domain IN (
            'cardiorespiratory','vascular','radiation','gravity','fitness',
            'bone','vision','immune','sleep','cabin','microbiology','medicalops'
        )),
    metric_code text NOT NULL
        CHECK (metric_code IN (
            'HR','SpO2','RR','BP_SYS','VASCULAR_INDEX','DOSE_MSV','GRAVITY_G',
            'EXERCISE_MIN','BONE_INDEX','OCT_INDEX','IMMUNE_INDEX',
            'SLEEP_H','CO2_PPM','CULTURE_INDEX','CHECKIN_COUNT'
        )),
    value numeric(14,3) NOT NULL CHECK (value >= 0 AND value <= 10000),
    unit text NOT NULL CHECK (length(unit) BETWEEN 1 AND 24),
    measured_at timestamptz NOT NULL,
    quality text NOT NULL DEFAULT 'VALID'
        CHECK (quality = 'VALID'),
    verification text NOT NULL DEFAULT 'UNVERIFIED'
        CHECK (verification = 'UNVERIFIED'),
    source_type text NOT NULL DEFAULT 'SIMULATED'
        CHECK (source_type = 'SIMULATED'),
    is_synthetic boolean NOT NULL DEFAULT true CHECK (is_synthetic IS TRUE),
    approved_for_public boolean NOT NULL DEFAULT false,
    approval_version text NOT NULL DEFAULT '2026-11-16-synthetic-seed-v1'
        CHECK (length(approval_version) BETWEEN 1 AND 64)
);
COMMENT ON TABLE public.rocketpulse_public_demo_samples IS
  'Isolated synthetic-only public display feed. NOT actual crew or clinical records.';

-- The public role may only read approved synthetic rows.
ALTER TABLE public.rocketpulse_public_demo_samples ENABLE ROW LEVEL SECURITY;
REVOKE ALL PRIVILEGES ON TABLE public.rocketpulse_public_demo_samples
    FROM PUBLIC, anon, authenticated;
DROP POLICY IF EXISTS rocketpulse_public_approved_synthetic_read
    ON public.rocketpulse_public_demo_samples;
CREATE POLICY rocketpulse_public_approved_synthetic_read
    ON public.rocketpulse_public_demo_samples
    FOR SELECT TO anon
    USING (
        approved_for_public IS TRUE
        AND is_synthetic IS TRUE
        AND source_type = 'SIMULATED'
        AND mission_id = 'DEMO-01'
    );
GRANT SELECT ON TABLE public.rocketpulse_public_demo_samples TO anon;

-- Stable, synthetic, historical 24-hour chart. No patient or device IDs.
WITH synthetic_crew AS (
    SELECT i, ('CREW-0' || i::text) AS crew
    FROM generate_series(1,4) AS i
), generated AS (
    SELECT
        'RP-PUBLIC-' || c.crew || '-' || m.metric_code || '-' ||
            lpad(t.slot::text,2,'0') AS event_id,
        c.crew AS astronaut_code,
        m.metric_code,
        m.unit,
        CASE m.metric_code
            WHEN 'HR' THEN 69 + c.i*2 + t.slot%8
            WHEN 'SpO2' THEN 96 + (c.i+t.slot)%3
            WHEN 'RR' THEN 12 + (c.i+t.slot)%6
            WHEN 'BP_SYS' THEN 112 + c.i*2 + t.slot%7
        END AS value,
        timestamptz '2026-11-16 10:00:00+00'
            - (23 - t.slot) * interval '1 hour' AS measured_at
    FROM synthetic_crew c
    CROSS JOIN generate_series(0,23) AS t(slot)
    CROSS JOIN (VALUES
        ('HR','bpm'), ('SpO2','%'), ('RR','breaths/min'), ('BP_SYS','mmHg')
    ) AS m(metric_code,unit)
)
INSERT INTO public.rocketpulse_public_demo_samples (
    event_id,mission_id,astronaut_code,domain,metric_code,
    value,unit,measured_at,quality,verification,source_type,
    is_synthetic,approved_for_public,approval_version
)
SELECT event_id,'DEMO-01',astronaut_code,'cardiorespiratory',
    metric_code,value,unit,measured_at,'VALID','UNVERIFIED','SIMULATED',
    true,true,'2026-11-16-synthetic-seed-v1'
FROM generated
ON CONFLICT (event_id) DO NOTHING;

-- One non-clinical placeholder signal for each of the other monitoring
-- domains, per fictional crew member. "INDEX" is an illustration only.
WITH synthetic_crew AS (
    SELECT i, ('CREW-0' || i::text) AS crew
    FROM generate_series(1,4) AS i
), examples(domain,metric_code,value,unit) AS (
    VALUES
      ('vascular','VASCULAR_INDEX',1.000::numeric,'index'),
      ('radiation','DOSE_MSV',0.180::numeric,'mSv'),
      ('gravity','GRAVITY_G',0.000::numeric,'g'),
      ('fitness','EXERCISE_MIN',45.000::numeric,'min'),
      ('bone','BONE_INDEX',1.000::numeric,'index'),
      ('vision','OCT_INDEX',1.000::numeric,'index'),
      ('immune','IMMUNE_INDEX',1.000::numeric,'index'),
      ('sleep','SLEEP_H',7.500::numeric,'h'),
      ('cabin','CO2_PPM',650.000::numeric,'ppm'),
      ('microbiology','CULTURE_INDEX',0.000::numeric,'index'),
      ('medicalops','CHECKIN_COUNT',1.000::numeric,'count')
)
INSERT INTO public.rocketpulse_public_demo_samples (
    event_id,mission_id,astronaut_code,domain,metric_code,
    value,unit,measured_at,quality,verification,source_type,
    is_synthetic,approved_for_public,approval_version
)
SELECT 'RP-PUBLIC-' || c.crew || '-' || e.metric_code,
    'DEMO-01',c.crew,e.domain,e.metric_code,e.value,e.unit,
    timestamptz '2026-11-16 10:00:00+00',
    'VALID','UNVERIFIED','SIMULATED',true,true,
    '2026-11-16-synthetic-seed-v1'
FROM synthetic_crew c CROSS JOIN examples e
ON CONFLICT (event_id) DO NOTHING;
COMMIT;

-- Verify: no anonymous writes, all rows synthetic, approved count > 0.
SELECT
    (SELECT count(*) FROM public.rocketpulse_public_demo_samples)
        AS total_synthetic_rows,
    (SELECT count(*) FROM public.rocketpulse_public_demo_samples
        WHERE approved_for_public AND is_synthetic AND source_type = 'SIMULATED')
        AS approved_synthetic_rows,
    has_table_privilege('anon',
        'public.rocketpulse_public_demo_samples','SELECT')
        AS anon_can_select,
    has_table_privilege('anon',
        'public.rocketpulse_public_demo_samples','INSERT')
        AS anon_can_insert,
    has_table_privilege('anon',
        'public.rocketpulse_public_demo_samples','UPDATE')
        AS anon_can_update,
    has_table_privilege('anon',
        'public.rocketpulse_public_demo_samples','DELETE')
        AS anon_can_delete,
    (SELECT relrowsecurity FROM pg_class
        WHERE oid='public.rocketpulse_public_demo_samples'::regclass)
        AS rls_enabled;

-- Check the actual anonymous view, not only table-owner counts:
BEGIN;
SET LOCAL ROLE anon;
SELECT count(*) AS visible_to_anonymous
FROM public.rocketpulse_public_demo_samples;
ROLLBACK;
