-- TeamRocket: live cloud sync readiness, read-only.
-- Run ONLY in TeamRocketV2Database / SQL Editor.
-- Never paste tokens, passwords, or secret keys into the SQL Editor.
-- This one SELECT returns one JSON report and performs NO changes.
WITH rpc AS (
 SELECT jsonb_build_object(
   'signature', p.oid::regprocedure::text,
   'security_definer', p.prosecdef,
   'function_owner', pg_get_userbyid(p.proowner),
   'function_settings', coalesce(to_jsonb(p.proconfig), '[]'::jsonb),
   'anon_can_execute', has_function_privilege('anon', p.oid, 'EXECUTE'),
   'authenticated_can_execute', has_function_privilege('authenticated', p.oid, 'EXECUTE')
 ) AS info
 FROM pg_proc p
 JOIN pg_namespace n ON n.oid = p.pronamespace
 WHERE n.nspname = 'public' AND p.proname = 'ingest_sync_event'
), policies AS (
 SELECT coalesce(jsonb_agg(jsonb_build_object(
   'table', tablename, 'policy', policyname, 'roles', roles,
   'command', cmd, 'using', qual, 'with_check', with_check
 ) ORDER BY tablename, policyname), '[]'::jsonb) AS rows
 FROM pg_policies
 WHERE schemaname='public'
 AND tablename IN (
   'missions','mission_members','astronauts','health_logs',
   'clinical_records','sync_receipts','sync_audit_log'
 )
), tables AS (
 SELECT jsonb_build_object(
   'required_total', count(*),
   'with_rls', count(*) FILTER(WHERE c.relrowsecurity),
   'no_policies', jsonb_agg(c.relname) FILTER(WHERE NOT EXISTS(
     SELECT 1 FROM pg_policies p
     WHERE p.schemaname = 'public' AND p.tablename = c.relname))
 ) AS summary
 FROM pg_class c
 JOIN pg_namespace n ON n.oid=c.relnamespace
 WHERE n.nspname='public' AND c.relkind IN ('r','p')
 AND c.relname IN (
   'missions','mission_members','astronauts','health_logs',
   'clinical_records','sync_receipts','sync_audit_log'
 )
)
SELECT jsonb_pretty(jsonb_build_object(
  'project', current_database(),
  'checked_at_utc', now() AT TIME ZONE 'UTC',
  'rpc', (SELECT coalesce(jsonb_agg(info), '[]'::jsonb) FROM rpc),
  'tables', (SELECT summary FROM tables),
  'policies', (SELECT rows FROM policies),
  'mission_members_total', (SELECT count(*) FROM public.mission_members),
  'demo_01_members', (SELECT count(*) FROM public.mission_members WHERE mission_id='DEMO-01'),
  'demo_02_members', (SELECT count(*) FROM public.mission_members WHERE mission_id='DEMO-02'),
  'astronauts_total', (SELECT count(*) FROM public.astronauts),
  'sync_receipts_total', (SELECT count(*) FROM public.sync_receipts)
)) AS teamrocket_live_sync_preflight;
