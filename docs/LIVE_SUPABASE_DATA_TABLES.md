# Live Supabase Data Tables — public metadata contract

## Why Data Tables previously showed "NOT VERIFIED"

The `/data-model` UI was a static PDF starter-field catalog. It did not call a database API, so the label stayed hardcoded even after the Supabase migration and test seeds.

## New path

`Vercel /data-model` → `GET /api/v1/public/schema/catalog` → Railway FastAPI → Supabase PostgREST (publishable key and anonymous RLS) → `public.rocketpulse_public_schema_catalog`.

This is a **read-only, operator-refreshed schema metadata snapshot**, not direct browser access to clinical tables. The UI shows the last verified snapshot timestamp, 57 expected tables, verified starter-field status, and (where explicitly approved) **counts of tagged deterministic synthetic seed rows**, not unrestricted full table counts. Missing/unpublished counts appear as "Not published", never zero. Refreshing the UI refetches the existing approved snapshot; trusted SQL `supabase/queries/refresh_public_schema_catalog_20261117.sql` must be rerun by an operator to refresh physical schema observations.

## Database setup and security

- `supabase/migrations/20261117_05_approved_schema_catalog.sql` creates the separate metadata-only table, RLS and anon-only SELECT policy. It was applied to the connected TeamRocket Supabase project.
- `supabase/queries/refresh_public_schema_catalog_20261117.sql` inspects `information_schema` under an authorized database operator and publishes only 57 known names and starter-field status. It checks known synthetic-only seed prefixes/identifiers for 16 explicitly enumerated tables. It does not publish individual astronaut records, clinical measurements, full counts of protected clinical tables, private identifiers, keys, queries, row values or incident details.
- `anon` can SELECT approved catalog rows, but cannot INSERT/UPDATE/DELETE. Private canonical RLS policies remain unchanged.
- The existing public approved measurement feed is **still** `rocketpulse_public_demo_samples`; this catalog is not an alternative read API for private clinical records.
- At migration inspection the catalog had 57 approved rows and all 57 starter field sets matched; this is **not** proof that 57 clinical workflows have been accepted.
- Extra canonical fields, indexes, foreign keys, constraints, authorized write/read APIs, true offline sync and 12 complete scenario executions require separate acceptance gates.

## Tests

Backend: `cd backend && python -m unittest app.tests.test_public_demo_api` (or repository integration pytest job). Public catalog schema validation enforces expected table names, approved labels, timestamps, scalar types and strict source provenance.

Frontend: `cd frontend && npm ci && npm run build && npm run test:database-ui`. Playwright asserts the Data Tables page requests `/api/v1/public/schema/catalog`, displays the synthetic-only seeded count, and clears stale readings if the API fails.

Live acceptance should include `GET https://teamrocket-rocketpulse.vercel.app/api/v1/public/schema/catalog` returning HTTP 200 and `source=supabase-approved-schema-snapshot` with `verified_tables=57`. Protected `/api/v1/missions/DEMO-01/command` must still reject anonymous requests. Neither the catalog nor the Vercel frontend should contain a service-role key.
