-- TeamRocket safe, read-only Supabase integration preflight.
-- Run in the Supabase SQL Editor of your DEVELOPMENT project.
-- This script DOES NOT create/modify tables, functions, policies, or data.
-- Review the results before applying any migrations.
WITH base AS (
  SELECT jsonb_build_object(
    'database', current_database(),
    'checked_at_utc', to_char(now() AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
    'table_counts', (
      SELECT jsonb_build_object(
        'public_tables', count(*),
        'rls_enabled', count(*) FILTER (WHERE c.relrowsecurity),
        'rls_forced', count(*) FILTER (WHERE c.relforcerowsecurity)
      )
      FROM pg_class c
      JOIN pg_namespace n ON n.oid = c.relnamespace
      WHERE n.nspname = 'public' AND c.relkind IN ('r','p')
    ),
    'required_tables', (
      SELECT jsonb_object_agg(t.table_name, to_regclass('public.'||t.table_name) IS NOT NULL)
      FROM (VALUES
        ('missions'), ('mission_members'), ('astronauts'),
        ('health_logs'), ('clinical_records'), ('sync_receipts'),
        ('sync_audit_log')
      ) AS t(table_name)
    ),
    'required_columns', (
      SELECT coalesce(jsonb_object_agg(v.full_name, v.present), '{}'::jsonb)
      FROM (
        SELECT t.table_name||'.'||t.column_name AS full_name,
          EXISTS (
            SELECT 1 FROM information_schema.columns c
            WHERE c.table_schema = 'public'
              AND c.table_name = t.table_name
              AND c.column_name = t.column_name
          ) AS present
        FROM (VALUES
          ('astronauts','crew_code'),
          ('health_logs','mission_id'),
          ('health_logs','astronaut_id'),
          ('sync_receipts','event_id'),
          ('mission_members','mission_id')
        ) t(table_name, column_name)
      ) v
    ),
    'sync_rpcs', (
      SELECT coalesce(jsonb_agg(jsonb_build_object(
        'signature', p.oid::regprocedure::text,
        'security_definer', p.prosecdef
      )), '[]'::jsonb)
      FROM pg_proc p
      JOIN pg_namespace n ON n.oid = p.pronamespace
      WHERE n.nspname = 'public'
        AND p.proname = 'ingest_sync_event'
    ),
    'table_access', (
      SELECT coalesce(jsonb_agg(jsonb_build_object(
        'table', c.relname,
        'rls_enabled', c.relrowsecurity,
        'anon_select_grant', has_table_privilege('anon', c.oid, 'SELECT'),
        'authenticated_select_grant', has_table_privilege('authenticated', c.oid, 'SELECT'),
        'policy_count', (
          SELECT count(*) FROM pg_policies q
          WHERE q.schemaname = 'public' AND q.tablename = c.relname
        )
      ) ORDER BY c.relname), '[]'::jsonb)
      FROM pg_class c
      JOIN pg_namespace n ON n.oid = c.relnamespace
      WHERE n.nspname = 'public' AND c.relkind IN ('r','p')
        AND c.relname IN (
          'missions','mission_members','astronauts','health_logs',
          'clinical_records','sync_receipts','sync_audit_log'
        )
    )
  ) AS result
)
SELECT jsonb_pretty(result) AS teamrocket_preflight_report FROM base;
