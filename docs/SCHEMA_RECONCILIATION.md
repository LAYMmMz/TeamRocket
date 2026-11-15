# Schema reconciliation — final PDF controls

Reviewed the existing repository `DatabaseSchema.md` and the 13-page final PDF. Do not blindly create duplicate tables to satisfy both documents. The final PDF states that its decisions control conflicts. Database changes are intentionally left to the database owner; the existing file was not modified.

| Existing repository term | Final PDF canonical term | Required reconciliation |
|---|---|---|
| `health_logs` wide telemetry row | `vital_signs` metric/value row | Normalize one metric per observation; retain event provenance. Gravity/functional observations belong to their own canonical domains. |
| `ultrasound_exams` | `vascular_ultrasound_results` | Preserve vein, side, flow, finding, examiner review and report attachment. |
| `approved_procedures` | `medical_procedures` + `procedure_steps` | Store explicit version, approval state, validity and ordered acknowledgments. |
| `incidents` | `medical_incidents` | Retain immutable `incident_events`. |
| `source_files` | `attachments` + `data_import_batches` | Storage reference/hash/access classification belongs to attachments; import provenance belongs to batches. |
| `quality_status` | canonical API `quality` | Adapter maps enums explicitly; unknown must not become valid. |
| `verification_status` | canonical API `verification` | Preserve review state separately; never conflate device validity and clinical review. |
| `original_value`, `normalized_value` | canonical API `value` | Return a verified normalized value only if normalization is defined; otherwise raw value with matching unit. Never pick value and unit from different representations. |
| `original_unit`, `normalized_unit` | canonical API `unit` | Quantity-aware mapping, no implicit dose conversion. |
| Direct Supabase client / Next.js | React TypeScript → FastAPI → SQLite/Supabase | This frontend is Vite React, compatible with Vercel. No direct DB access. |

The final PDF lists UUID IDs, UTC timestamps, foreign keys, immutable event IDs, no destructive medical cascades, RLS, distinct receipt times, and synthetic provenance. The UI's simplified presentation DTOs are not SQL migrations. The backend must join and transform canonical records into the DTOs, while retaining underlying typed evidence links and audit metadata.

The cloud `sync_queue` and onboard SQLite `sync_queue` are separate physical stores. Do not confuse a browser demo receipt with either store.
