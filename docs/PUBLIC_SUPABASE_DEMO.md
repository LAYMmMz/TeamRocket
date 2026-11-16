# RocketPulse — login-free, real Supabase-backed synthetic dashboard

## Boundaries

The public dashboard uses **real reads from Supabase** but the dataset itself is **synthetic research demonstration data**, not astronaut health records. Supabase's protected `health_logs`, `astronauts`, `clinical_records`, `mission_members`, and `ingest_sync_event` RPC are never anonymously queried or granted new privileges.

```text
Anonymous visitor
  -> Vercel (React, VITE_DATA_MODE=public)
  -> same-origin GET /api/v1/public/...
  -> Railway FastAPI (read-only allowlisted projection)
  -> Supabase PostgREST /rocketpulse_public_demo_samples
     using *only* the publishable key / anon role + strict RLS
```

The server selects a fixed set of fields and applies `approved_for_public=true`, `is_synthetic=true`, `source_type=SIMULATED`, `mission_id=DEMO-01` and an allowlisted crew/domain. It also validates returned rows, limits response sizes and sets a 30-second response cache. No free-text notes, authentication metadata or private table records can be included. Protected endpoints continue to require JWTs; all public POST/PUT/PATCH/DELETE operations are disabled.

## One-time database setup (manual, audited)

**Important:** ChatGPT's Supabase connector is currently signed into a different organization and cannot see `TeamRocketV2Database`, project `ziecxjoeljxoocixejtz`. Therefore **this SQL has not been executed and the new table does not exist until the project owner runs it**.

1. As the TeamRocket database owner, review `supabase/manual/20261116_public_demo_feed.sql` before executing it in the **correct production project** SQL Editor. It creates only `public.rocketpulse_public_demo_samples`, grants `anon SELECT` with a strict RLS policy, disallows anonymous writes and seeds 428 predictable **synthetic-only, public-approved** measurement rows. The seed is idempotent; rerunning does not overwrite approved statuses or modify existing data.
2. Run the final verification SELECT. Expected `total_synthetic_rows >= 428`, `approved_synthetic_rows >= 428`, `anon_can_select=true`, `anon_can_insert/update/delete=false`, `rls_enabled=true`, and `visible_to_anonymous >= 428`. If any values differ, **stop**, inspect the state and do not broaden RLS permissions on clinical tables.
3. Only then enable `VITE_DATA_MODE=public` on the desired **Vercel Preview** branch and redeploy. Use `VITE_API_BASE_URL=/api/v1`, which targets the existing Railway rewrite. Production demo mode should remain until the preview is verified.
4. Test without login:
   - `GET /api/v1/public/missions/DEMO-01/command?astronaut_id=CREW-01` returns JSON with `data_source=supabase-approved-synthetic`, only fake crew codes and explicitly synthetic vitals.
   - `GET /api/v1/public/measurements/trends?astronaut_id=CREW-01` returns the historical synthetic chart.
   - `GET /api/v1/public/reports/domains/cabin?astronaut_id=CREW-01` returns only approved synthetic domain metrics.
   - `GET /api/v1/missions/DEMO-01/command?astronaut_id=CREW-01` **without auth** must still return **401 Unauthorized**.
   - `POST /api/v1/public/measurements/trends` must return **405 Method Not Allowed**.
5. The public dashboard **fails closed** with a clear data-link error and no fake fallback if the Supabase table is missing, empty, or unavailable. This prevents falsely claiming to be database-backed when only static fixtures were loaded.

## Data hygiene and safety

- Only four generic crew codes, 15 bounded metric names, 12 domain names, numeric values, units and historical timestamps are in the public table. No identifiable persons, notes, private audit logs, user metadata or clinical threshold decisions are exposed.
- The synthetic seed sets `quality=VALID` and `verification=UNVERIFIED` to avoid describing medically validated evidence. It is **not a certified medical device**.
- Do not use `service_role`, database passwords, or privileged RPCs in browser code or in the public adapter. Railway's existing variable `SUPABASE_ANON_KEY` must contain **only** the public `sb_publishable_` key.
- Never clone or promote private `health_logs` records to the public feed without independent approval and de-identification review.
- Any changes to dashboard data beyond the synthetic seed should be made by a reviewed, privileged SQL operator—not by an anonymous API endpoint. Avoid exposing INSERT/UPDATE/DELETE permissions in Supabase.
- The protected mission sync worker remains separate and its long-lived background worker is still disabled.

## Status

- GitHub integration branch: `feat/frontend-backend-api-integration`; draft PR #4, no merge.
- FastAPI route implementation and automated tests are committed.
- **Cloud readiness remains pending the owner's explicit execution of the new SQL file in the correct Supabase project**, plus public endpoint live validation. Do not mark real database reads verified until the endpoint returns at least one row and the synthetic source marker is present.
