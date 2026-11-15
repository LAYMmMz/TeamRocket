# Supabase Cloud Ingestion Acceptance Test Results

**Date:** 2026-11-15  
**Environment:** Supabase Project (`ziecxjoeljxoocixejtz`) — `Database` Branch  
**Target RPC:** `public.ingest_sync_event(p_event JSONB)`  
**Domain Table:** `public.health_logs`  
**Receipt & Audit Tables:** `public.sync_receipts`, `public.sync_audit_log`

---

## Summary of Acceptance Checks

| # | Test Case | Expected Behavior | HTTP Status | Result |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **Authorized Write** | Authenticated user ingests event; writes to `health_logs`, issues `receipt_id`, logs `INGESTED`. | `200` | **PASS** |
| **2** | **Idempotent Retry** | Re-sending identical `event_id` + `payload_hash` returns original `receipt_id` without duplicate writes. | `200` | **PASS** |
| **3** | **Hash Conflict Rejection** | Re-sending `event_id` with modified `payload_hash` is rejected with `23505` conflict and logged. | `409` | **PASS** |
| **4a** | **Unauthenticated RPC Block** | Calling `ingest_sync_event` without a valid JWT is rejected with `28000` Unauthorized. | `403` | **PASS** |
| **4b** | **RLS Direct Table Isolation** | Direct `anon` REST query against `public.sync_receipts` returns 0 rows (`[]`). | `200` | **PASS** |
| **5** | **Immutable Audit Trail** | `public.sync_audit_log` preserves both `INGESTED` and `CONFLICT_REJECTED` entries with original hash intact. | SQL Verified | **PASS** |

---

## Sanitized Execution Outputs

### Test 1 — Authorized Write
```json
{
  "event_id": "11111111-1111-4111-8111-111111111111",
  "receipt_id": "a1e33d03-326b-47cf-9dce-a80094a5fca2",
  "payload_hash": "sha256_valid_hash_001"
}


{
  "code": "23505",
  "details": null,
  "hint": null,
  "message": "Conflict: event_id 11111111-1111-4111-8111-111111111111 already exists with a different payload_hash"
}



{
  "code": "28000",
  "details": null,
  "hint": null,
  "message": "Unauthorized: authenticated user JWT required"
}
