-- SECURITY HOTFIX FOR EXISTING TeamRocketV2Database PROJECT ONLY
-- Project reference: ziecxjoeljxoocixejtz.
-- NOT an automatic migration or a fresh database bootstrap.
-- Do not execute until a project owner reviews the exact changes.
-- This changes grants and one RLS policy, but never deletes tables or data.
-- The transaction aborts without changes if the expected policies differ.

BEGIN;

DO $guard$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_proc
        WHERE oid = 'public.ingest_sync_event(jsonb)'::regprocedure
          AND prosecdef
    ) THEN
        RAISE EXCEPTION 'Abort: expected privileged sync RPC missing or changed';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'health_logs'
          AND policyname = 'Enable all access for hackathon on health_logs'
          AND cmd = 'ALL'
          AND 'public' = ANY(roles)
          AND qual = 'true'
          AND with_check = 'true'
    ) THEN
        RAISE EXCEPTION 'Abort: unrestricted health_logs policy differs from audit';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'health_logs'
          AND policyname = 'health_logs_read_mission_members'
          AND cmd = 'SELECT'
          AND 'authenticated' = ANY(roles)
    ) THEN
        RAISE EXCEPTION 'Abort: mission-scoped health_logs SELECT policy missing';
    END IF;
END
$guard$;

-- Restrict the elevated RPC to authenticated accounts. Revoke PUBLIC
-- as well as anon, since anon can inherit PUBLIC function privileges.
REVOKE EXECUTE ON FUNCTION public.ingest_sync_event(jsonb) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.ingest_sync_event(jsonb) FROM anon;
GRANT EXECUTE ON FUNCTION public.ingest_sync_event(jsonb) TO authenticated;

-- Drop only the exact audited open-door policy. Preserve the existing
-- per-mission policy health_logs_read_mission_members.
DROP POLICY "Enable all access for hackathon on health_logs"
ON public.health_logs;

-- Defense in depth: do not permit browser anon direct table operations.
-- Keep SELECT for authenticated users, still filtered by the RLS policy.
-- The intended write path is the authenticated RPC, not browser table DML.
REVOKE ALL PRIVILEGES ON TABLE public.health_logs FROM anon;
REVOKE ALL PRIVILEGES ON TABLE public.health_logs FROM PUBLIC;
GRANT SELECT ON TABLE public.health_logs TO authenticated;

COMMIT;

-- Post-change verification. Expected:
-- anon_rpc_execute=false, authenticated_rpc_execute=true,
-- anon_health_logs_select_grant=false, mission_policy_present=true,
-- unrestricted_policy_present=false.
SELECT
    has_function_privilege(
        'anon', 'public.ingest_sync_event(jsonb)', 'EXECUTE'
    ) AS anon_rpc_execute,
    has_function_privilege(
        'authenticated', 'public.ingest_sync_event(jsonb)', 'EXECUTE'
    ) AS authenticated_rpc_execute,
    has_table_privilege(
        'anon', 'public.health_logs', 'SELECT'
    ) AS anon_health_logs_select_grant,
    has_table_privilege(
        'authenticated', 'public.health_logs', 'SELECT'
    ) AS authenticated_health_logs_select_grant,
    EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'health_logs'
          AND policyname = 'health_logs_read_mission_members'
    ) AS mission_policy_present,
    EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'health_logs'
          AND policyname = 'Enable all access for hackathon on health_logs'
    ) AS unrestricted_policy_present,
    has_schema_privilege('anon', 'public', 'CREATE')
        AS anon_can_create_objects_in_public,
    has_schema_privilege('authenticated', 'public', 'CREATE')
        AS authenticated_can_create_objects_in_public;
