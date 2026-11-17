# Workflow → database integration (2026-11-17)

## Data path
The public, no-login judge deployment uses **Vercel React → `/api/v1/public/…` FastAPI on Railway → Supabase PostgREST with publishable/anon key → `public.rocketpulse_public_demo_samples`**. FastAPI validates mission, crew, source, unit, quality, synthetic label, and approval before returning records. Protected API mode still uses authorized FastAPI, onboard SQLite and queued cloud sync; it is not made public by this change.

| Workflow menu | Connected behavior | Source and limitations |
|---|---|---|
| Crew Health Explorer (`/explorer`) | 3D body region selects health domain and obtains selected crew's records via `/reports/domains/{domain}`. | Approved synthetic database samples in public mode; no diagnostic 3D scan. Existing path. |
| Health Systems (`/domains`, `/domains/:id`) | Each of 12 domain detail pages loads source-tagged readings via the same FastAPI endpoint; switching crew aborts stale requests. | Unsupported legacy pseudo-indices are filtered. Missing data stays missing. Existing path. |
| Medical Alerts & Events (`/cases`) | Adds selected-crew medical-operations records from `medicalops` API domain (public synthetic `CHECKIN_COUNT` sample), while authenticated alert acknowledgment and symptom submissions continue through protected FastAPI paths. | Public records are **not** incidents/alerts and cannot be acknowledged or edited; public true clinical alerts remain private. |
| Mission Scenarios (`/simulation`) | Selecting S01–S09 loads only relevant approved domain records for the selected crew, shows actual source table and missing/error states. | The scenario definition and expected outcome remain static reference material, **not executed end-to-end test results**. S10–S12 require protected audit/sync/procedure testing; do not invent public records or success. |

## Verified database facts at inspection time
- Connected project: `TeamRocketV2Database` (`ziecxjoeljxoocixejtz`).
- SQL `SELECT` returned **428 approved synthetic records** across 12 domain labels and 4 fictional crew identifiers.
- `anon` had SELECT but not INSERT, UPDATE, or DELETE privilege on the isolated synthetic feed.
- The canonical mission/clinical tables remain protected by row-level security; their actual end-to-end clinical workflows are **not verified** by this UI change.
- **No Supabase schema, permissions, stored clinical records, or production deployment were changed.** This branch changes application read wiring and test assertions only.

## Test plan
1. `cd frontend && npm ci && npm run check:scope && npm run build`.
2. `npm run dev` with `VITE_DATA_MODE=public` and API proxy configured; open `/explorer` and `/domains/medicalops`, change selected crew, verify record IDs/source table change without mixing crews.
3. Open `/cases`: medical-ops samples load, but symptom/acknowledgment write controls remain unavailable in public mode.
4. Open `/simulation`: S04 fetches `cabin` and `medicalops`; S07 fetches `radiation`. S05–S06 must show missing method-specific evidence, and S10–S12 must not claim database execution.
5. Disable the API or return 503: affected workflow panels show failure rather than fabricated values.
6. Run `npm run test:database-ui` with the project Chromium/Playwright environment. This uses mocked FastAPI responses; it does not certify live end-to-end behavior.

## Deployment gate
Merge this branch after checks and deploy the frontend to the existing Vercel project. The existing Railway backend routes are reused; there is **no new Supabase migration or environment variable**. The live browser must independently be checked after Vercel/Railway deployments. Full clinical workflow writes, all 57 canonical table behaviors, and S01–S12 end-to-end outcomes remain separate release gates.
