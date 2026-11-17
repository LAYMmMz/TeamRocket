-- Public, non-identifying metadata snapshot for the RocketPulse judge dashboard.
-- This is a curated publication surface, NOT a security-definer read of private
-- medical tables or a client permission escalation.
CREATE TABLE IF NOT EXISTS public.rocketpulse_public_schema_catalog (
    table_name text PRIMARY KEY CHECK (table_name ~ '^[a-z][a-z0-9_]{1,62}$'),
    table_present boolean NOT NULL,
    starter_fields_verified boolean NOT NULL,
    starter_field_count integer NOT NULL CHECK (starter_field_count BETWEEN 1 AND 100),
    missing_starter_fields text[] NOT NULL DEFAULT '{}',
    published_synthetic_rows integer NULL CHECK (published_synthetic_rows BETWEEN 0 AND 10000000),
    inspected_at timestamptz NOT NULL,
    approved_for_public boolean NOT NULL DEFAULT false,
    source_label text NOT NULL DEFAULT 'verified_supabase_metadata_snapshot'
      CHECK (source_label = 'verified_supabase_metadata_snapshot'),
    CONSTRAINT consistent_catalog_status CHECK (
        NOT starter_fields_verified OR (
            table_present AND cardinality(missing_starter_fields) = 0
        )
    )
);
COMMENT ON TABLE public.rocketpulse_public_schema_catalog IS
  'Approved schema metadata snapshot and counts of deterministic test-only seed rows. Never contains clinical rows, personal identifiers or private table-wide counts. Refresh requires trusted SQL execution.';
ALTER TABLE public.rocketpulse_public_schema_catalog ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.rocketpulse_public_schema_catalog FROM PUBLIC, anon, authenticated;
GRANT SELECT ON public.rocketpulse_public_schema_catalog TO anon, authenticated;
DROP POLICY IF EXISTS rocketpulse_public_schema_metadata_read ON public.rocketpulse_public_schema_catalog;
CREATE POLICY rocketpulse_public_schema_metadata_read
 ON public.rocketpulse_public_schema_catalog FOR SELECT TO anon, authenticated
 USING (approved_for_public IS TRUE);
-- No public write policy and no public DML grant.
