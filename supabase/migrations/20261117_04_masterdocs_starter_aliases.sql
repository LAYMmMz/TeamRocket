-- MasterDocs §4 starter-field reconciliation for the EXISTING TeamRocket cloud schema.
-- Additive, legacy-compatible aliases: original_* stay authoritative for current
-- importers, but canonical PDF names are queryable and always synchronized.
-- Does not change RLS, anonymous privileges, private data or receipt history.
-- PG17 GENERATED STORED columns reject direct writes by design; API writes the
-- existing source columns. Do not change into writable columns without an adapter.
BEGIN;
ALTER TABLE public.personal_dose_records ADD COLUMN IF NOT EXISTS value numeric GENERATED ALWAYS AS (original_value) STORED;
ALTER TABLE public.personal_dose_records ADD COLUMN IF NOT EXISTS unit text GENERATED ALWAYS AS (original_unit) STORED;
ALTER TABLE public.radiation_area_records ADD COLUMN IF NOT EXISTS value numeric GENERATED ALWAYS AS (original_value) STORED;
ALTER TABLE public.environmental_readings ADD COLUMN IF NOT EXISTS value numeric GENERATED ALWAYS AS (original_value) STORED;
ALTER TABLE public.environmental_readings ADD COLUMN IF NOT EXISTS unit text GENERATED ALWAYS AS (original_unit) STORED;
ALTER TABLE public.sleep_sessions ADD COLUMN IF NOT EXISTS duration numeric GENERATED ALWAYS AS (original_value) STORED;
ALTER TABLE public.sleep_sessions ADD COLUMN IF NOT EXISTS source text GENERATED ALWAYS AS (source_type) STORED;
ALTER TABLE public.nutrition_logs ADD COLUMN IF NOT EXISTS meal_at timestamptz GENERATED ALWAYS AS (measured_at) STORED;
ALTER TABLE public.fluid_balance_logs ADD COLUMN IF NOT EXISTS unit text GENERATED ALWAYS AS (original_unit) STORED;
ALTER TABLE public.alert_evidence ADD COLUMN IF NOT EXISTS source_record_type text GENERATED ALWAYS AS (source_table_name) STORED;
-- Existing sync receipts are immutable successful cloud acknowledgments; expose
-- canonical naming while retaining receipt_id as the preexisting PRIMARY KEY.
ALTER TABLE public.sync_receipts ADD COLUMN IF NOT EXISTS id uuid GENERATED ALWAYS AS (receipt_id) STORED;
ALTER TABLE public.sync_receipts ADD COLUMN IF NOT EXISTS acknowledged_at timestamptz GENERATED ALWAYS AS (received_at) STORED;
ALTER TABLE public.sync_receipts ADD COLUMN IF NOT EXISTS remote_status text GENERATED ALWAYS AS ('ACKNOWLEDGED'::text) STORED;
COMMIT;
