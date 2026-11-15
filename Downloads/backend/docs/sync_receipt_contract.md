# Cloud Sync Receipt Contract (`v1.1`)

- **Project Reference:** `ziecxjoeljxoocixejtz`
- **Deployed RPC:** `public.ingest_sync_event(p_event JSONB)`
- **Permitted Role:** `authenticated` (`PUBLIC` revoked; executes as `SECURITY DEFINER` with `search_path = public`)
- **Authoritative Telemetry Table:** `public.health_logs`
- **Ledger, Membership & Audit Tables:** `public.sync_receipts`, `public.mission_members`, `public.sync_audit_log`

## Request Contract & Field Aliases
`POST /rest/v1/rpc/ingest_sync_event` with `Authorization: Bearer <user_jwt>`:
- Supports both Dev 1 queue keys (`metric`, `value`, `unit`, `quality`, `timestamp`, `crew_code`) and canonical keys (`metric_code`, `original_value`, `original_unit`, `quality_status`, `measured_at`, `astronaut_id`).
- Supported `kind` values: `measurement`, `vital_sign` (all other kinds are explicitly rejected with SQLSTATE `22023`).

```json
{
  "p_event": {
    "event_id": "measurement:22222222-2222-4222-8222-222222222222",
    "kind": "measurement",
    "record_id": "22222222-2222-4222-8222-222222222222",
    "mission_id": "DEMO-02",
    "payload_hash": "sha256_valid_hash_001",
    "immutable": true,
    "previous_hash": null,
    "payload": {
      "astronaut_id": "TEST-CREW-01",
      "source_device_id": "DEV-01",
      "source_type": "SIMULATED",
      "metric": "heart_rate",
      "value": 72,
      "unit": "bpm",
      "quality": "Valid",
      "timestamp": "2026-11-15T14:00:00Z"
    },
    "audit_event": {
      "source": "offline_outbox_worker"
    }
  }
}