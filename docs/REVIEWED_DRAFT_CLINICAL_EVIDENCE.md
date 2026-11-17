# Reviewed draft integration — protected clinical evidence (2026-11-17)

The former `draft` branch contained nine unmerged commits. This branch selectively carries its **authorized, synthetic-only local SQLite** examination and laboratory readers, frontend components, local scenario reporting workflow and read-only Supabase schema preflight.

## What is integrated

- Protected `GET /api/v1/clinical/examinations/{astronaut_id}` and `/laboratory/{astronaut_id}` for mission-authorized `admin` or `flight_surgeon` principals in `development` / `test` and `DEMO-01` only.
- Synthetic local SQLite examinations: vascular ultrasound laterality, OCT by eye/region, ground-only bone DXA by region/phase, and fitness assessments; lab evidence: samples, assay-aware laboratory results, sequencing QC and sample custody. Missing evidence is not reported as normal or diagnosed.
- Authenticated (`VITE_DATA_MODE=api`) examination/laboratory dashboards can display this *local* evidence through FastAPI, never in public mode.
- A local scenario report generator and CI artifact, explicitly labelled **not proof of actual cloud receipt or deployed scenario acceptance**.
- A read-only 57-table starter-field and RLS-enabled preflight query against an authorized Supabase SQL session.

## Safety adjustments compared with the original draft

- **Removed the unscoped medical exam schedule query from the new endpoint.** That model lacks a synthetic flag and directly selecting schedule rows could mix unreviewed schedule data with synthetic fixtures. Reintroduce only after explicit synthetic provenance and mission scope exist.
- Did **not** copy or execute `supabase/manual/20261117_fresh_schema_57_table_DRAFT.sql`. Its 903-line proposed fresh-schema DDL is untested and conflicts with existing production schemas, keys and migrations.
- Did **not** overwrite the current root README or current frontend `api.ts` / `Dashboards.tsx` with stale `draft` revisions.
- No anonymous clinical record access, public clinical read policy, or service-role browser key was added.
- Nothing here changes the Supabase cloud 57-table data, seeds, RLS or receipts.

## Verification / limitations

- Backend tests: `cd backend && python -m unittest discover -s tests -t .`
- Frontend: `cd frontend && npm ci && npm run build && npm run test:database-ui`
- Local scenario report: `cd backend && python -m scripts.masterdocs_scenario_report`
- The public Vercel judge website remains `VITE_DATA_MODE=public`; additional clinical panels state that private evidence is not available in that mode. Unauthorized clinical API requests must receive HTTP 401/403.
- These endpoints use *local Dev2 SQLite*, not verified Supabase clinical reads. Do not claim G1–G6 or S01–S12 full acceptance.

After tests pass, a focused review can merge this branch into `main`. The original `draft` branch should be retained until its remaining schema proposal receives a separate review.
