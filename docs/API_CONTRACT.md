# Proposed FastAPI integration contract v1

The PDF specifies endpoint **families**, not final methods or JSON shapes. These are frontend proposals for agreement with your backend developer. Generate final TypeScript types from FastAPI OpenAPI after the backend is implemented; update `types.ts` and `service.ts` together. Do not claim these endpoints already exist.

## Boundary

React calls FastAPI only. FastAPI verifies Supabase JWT, mission membership and role, validates Pydantic input, commits onboard SQLite before sync, runs the shared Python rule engine, and manages Supabase writes. React never reads SQLite, embeds service-role secrets, calculates operational clinical thresholds, or publishes privileged Supabase writes.

The temporary API-mode account panel accepts an access token into memory for integration testing. Replace it with a proper Supabase Auth sign-in/session-refresh flow before using real records. Browser demo role switching is absent in API mode; `role` and `subject_id` come from the authorized backend response.

## Implemented adapter calls

Base URL: `VITE_API_BASE_URL`, e.g. `https://api.example.org/api/v1`.

| Method | Path | Request | Expected success |
|---|---|---|---|
| GET | `/reports/dashboard` | Bearer token, no client-authoritative role | `200 Snapshot` |
| POST | `/symptoms` | `Symptom` plus `event_id`; Idempotency-Key header | 201 JSON or 204 |
| POST | `/alerts/{id}/acknowledgments` | `{event_id}`; Idempotency-Key | 201 JSON or 204 |
| POST | `/reports/{id}/reviews` | `{event_id,note}`; Idempotency-Key | 201 JSON or 204 |

All requests have a 15-second timeout. Failed requests show an error, not a success notification. API mode does not silently fall back to fixtures. GET refreshes every 30 seconds; operational real-time transport and browser/background delivery guarantees are not implemented. Each POST currently creates a new event ID per user submission; the backend must enforce unique immutable IDs and make retry behavior explicit. The frontend does not auto-retry uncertain writes. Add a durable retry/outbox design with stable IDs before operational use.

## Snapshot response

Exact frontend interfaces are in `frontend/src/types.ts`. The response is a presentation aggregate, not a competing clinical database.

```ts
interface Snapshot {
  crew: Crew[];
  measurements: Measurement[];
  alerts: Alert[];
  records: DomainRecord[];
  events: Event[];
  role: Role;
  subject_id: string;
  simulation_time: string;
}
```

- `Crew`: `id` UUID, `crew_code`, `display_name`, `crew_role`, `color` (UI accent).
- `Measurement`: `id`, `astronaut_id`, `metric_code`, `value:number|null`, `unit`, `measured_at`, `received_at`, `source_device_id`, `quality:valid|suspect|missing|stale`, `verification`, `is_synthetic`, `baseline_value:number|null`, `history:number[]` ordered oldest first. Current charts are equal-interval daily display fixtures; replace history with timestamped points if intervals vary. Null readings never become zero or normal.
- `Alert`: `id`, nullable astronaut/location IDs, title, severity (`informational`, `advisory`, `warning`, `critical`, `data-unavailable`), status (`open`, `acknowledged`, `resolved`), `rule_id`, `rule_version`, `approval_status`, rendered evidence strings, created/acknowledged timestamps, incident ID, synthetic flag. Backend must retain typed evidence links in `alert_evidence`; strings are a display projection only.
- `DomainRecord`: `id`, nullable astronaut ID, domain, title, canonical `table`, value and unit for display, method, status, measured timestamp, source, string-valued detail metadata, synthetic flag. Backend must retain structured numeric values in canonical tables; do not persist these display strings as authoritative measurements.
- `Event`: immutable `event_id`, entity type, timestamp, status (`queued` or `received`), object payload. This simplified UI does not yet model all cloud/local receipt fields. Add `local_received_at`, `cloud_received_at`, `clinician_acknowledged_at`, receipts and conflict state to the production DTO without collapsing them.

The backend must supply full schema validation and authorization. The client validates measurements, alerts, role, and aggregate shape; expand runtime validation for additional DTOs when replacing fixture modules.

## Symptom input

```json
{
  "event_id": "<UUID>",
  "astronaut_id": "<authorized crew UUID>",
  "symptom_code": "breathing_difficulty",
  "severity": "severe",
  "onset_at": "2026-06-15T12:00:00Z",
  "notes": "Synthetic report",
  "is_synthetic": true
}
```

Server must enforce mission assignment, UTC time validity, allowed vocabulary and severity, maximum note length, anti-replay rules, audit ownership, and approved symptom workflow. The authenticated actor comes from JWT, never from a client-selected actor field. Rule approvals, findings and treatment authority cannot come from a browser role picker.

## Errors and security

- 401: expired or invalid token; clear state and sign in again.
- 403: role/mission scope forbidden; record denied-access audit without confidential content.
- 409: event/version conflict; surface review instead of overwrite.
- 422: field-level validation; adapt backend details into friendly form errors in the integration phase.
- 429/5xx: no false success; retry only with the same idempotency key after a defined receipt check.
- CORS must allow only authorized frontend origins. HTTPS for online traffic; onboard offline grants must be verified and expiring. RLS and Storage policies are backend/database acceptance gates.

## Remaining endpoint families and owners

`/auth /missions /astronauts /devices /measurements /samples /examinations /radiation /environment /incidents /procedures /inventory /sync` remain backend-owned. Add read/write clients per module as OpenAPI stabilizes. Browser UI lists data requirements; this release does not provide server implementations, upload adapters or migrations. Files remain in Supabase Storage with protected signed access, hashes and classifications; do not place real ECG/OCT/FASTQ content in this public repository.
