-- TeamRocket — read-only Supabase privileged RPC security audit.
-- Run in the CONFIRMED TeamRocketV2Database project SQL Editor.
-- Read-only: does not modify policies, functions, grants, or records.
SELECT
    p.oid::regprocedure::text AS function_name,
    p.prosecdef AS security_definer,
    has_function_privilege('anon', p.oid, 'EXECUTE') AS anon_can_execute,
    has_function_privilege('authenticated', p.oid, 'EXECUTE') AS authenticated_can_execute,
    has_function_privilege('service_role', p.oid, 'EXECUTE') AS service_role_can_execute,
    pg_get_userbyid(p.proowner) AS function_owner,
    p.proconfig AS function_settings
FROM pg_proc AS p
JOIN pg_namespace AS n ON n.oid = p.pronamespace
WHERE n.nspname = 'public'
  AND p.proname = 'ingest_sync_event';

-- Inspect only the policies required by the sync path.
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check
FROM pg_policies
WHERE schemaname = 'public'
  AND tablename IN (
      'mission_members', 'missions', 'astronauts',
      'health_logs', 'clinical_records', 'sync_receipts', 'sync_audit_log'
  )
ORDER BY tablename, policyname;

-- Ensure the expected membership data exists without exposing user identifiers.
SELECT
    (SELECT count(*) FROM public.mission_members) AS membership_records,
    (SELECT count(*) FROM public.astronauts) AS astronaut_records,
    (SELECT count(*) FROM public.missions) AS mission_records;
