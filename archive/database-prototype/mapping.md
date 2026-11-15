# TeamRocket: Local SQLite / Backend to Supabase Mapping

## 1. Sync Strategy & Auth Contract
- **Selected Strategy:** Single receipt-based RPC (`POST /rest/v1/rpc/ingest_sync_event`) driven by the `backend` branch's `sync_queue` worker. The direct table-upsert script in `Database` will be retired/aligned to emit `p_event` envelopes into `sync_queue`.
- **Authentication:** `apikey: <SUPABASE_PUBLISHABLE_KEY>` + `Authorization: Bearer <authenticated_user_jwt>` (user must belong to the target `mission_id`). Service-role keys are never exposed to the client or React frontend.

## 2. Table & Field Conversions
| Local / Backend Source | Cloud Destination | Field & Type Conversions |
| :--- | :--- | :--- |
| `vital_signs` (`kind: "measurement"`) | `public.vital_signs` *(or `health_logs` — confirm via `cloud_schema_full.csv`)* | `id` (UUID), `astronaut_id` (TEXT/UUID), `mission_id` (TEXT, required), `metric_code` (TEXT), `original_value` / `normalized_value` (FLOAT8), `quality_status` (`Valid` \| `Suspect` \| `Invalid`), `measured_at` (ISO-8601 UTC `TIMESTAMPTZ`). |
| `symptom_reports` (`kind: "symptom"`) | `public.symptom_reports` | `id` (UUID), `astronaut_id`, `mission_id`, `symptom_code`, `severity` (INT 1–10), `notes` (TEXT), `measured_at` (`TIMESTAMPTZ`). |
| `medical_procedures` | `public.approved_procedures` | Rename `steps_json` (SQLite `TEXT`) -> `steps` (`JSONB` via `::jsonb`). |
| `alert_rules` | `public.alert_rules` | Convert SQLite `version` (`INTEGER`, e.g., `1`) -> Cloud `version` (`TEXT` semantic version, e.g., `'1.0.0'`). |
| `sync_queue` / `sync_outbox` | `public.sync_receipts` + `public.sync_audit_log` | Transport envelope (`event_id`, `payload_hash`, `previous_hash`, `immutable`, `audit_event`) stored as immutable evidence; returns `{event_id, payload_hash, receipt_id}`. |