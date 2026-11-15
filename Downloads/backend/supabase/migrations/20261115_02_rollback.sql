cat << 'EOF' > supabase/migrations/20261115_02_rollback.sql
DROP FUNCTION IF EXISTS public.ingest_sync_event(JSONB);
EOF