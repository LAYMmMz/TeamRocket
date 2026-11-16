# RocketPulse frontend–backend integration (synthetic research prototype)

## Scope
This branch includes protected FastAPI `/api/v1` compatibility endpoints used by the active Vite dashboard, Supabase user login (not a service-role client), and a backend container recipe. The synthetic FastAPI staging service is deployed on Railway, but this does not configure Vercel, validate live Supabase RPC permissions, or pass the older backend's unresolved acceptance suite. Domain2 SQLite fixtures are exposed only for `APP_ENV=development/test` and `DEMO-01`, with synthetic flags. Production must not rely on those fixtures.

## Staging backend already deployed (2026-11-16)

- Railway project: `TeamRocket-Astronaut-Health` (private).
- Railway environment: `staging`; service: `teamrocket-fastapi`.
- Public staging endpoint: `https://teamrocket-fastapi-staging.up.railway.app/api/health`.
- GitHub integration branch: `feat/frontend-backend-api-integration`; Dockerfile at `backend/Dockerfile`, Railway root `railway.json`.
- Deployment reached Railway status `SUCCESS`, and runtime logs show successful FastAPI startup; no authenticated production end-to-end test has been completed.
- Persistent 500MB encrypted local SQLite volume mounted at `/data`.
- `APP_ENV=test`; **not a production environment**. Development/test synthetic-data paths are accessible only with valid authorized JWTs. No Dev1 development signing secret configured.
- The backend environment includes the **public** Supabase publishable key and the confirmed Supabase project URL; `SYNC_ACCESS_TOKEN` and `SYNC_RPC_URL` are deliberately unset pending live RPC permission review and identity setup. This backend is **not yet writing to Supabase**.
- Railway staging `CORS_ORIGINS` is currently `http://localhost:5173`; the real Vercel production/preview origin must be added separately. Do not add `*` for convenience.
- **Before enabling browser API mode**, configure Vercel environment variables and verify Supabase JWT algorithm, role mapping, and mission scope.

## Vercel frontend deployment — correct project and proxy

The active Vercel project is [team-rocket-rocket-pulse-front-end](https://vercel.com/laymmmzs-projects/team-rocket-rocket-pulse-front-end), configured with Root Directory `frontend`. The older `rocketpulse` project points to the obsolete `RocketPulse FrontEnd` directory and currently reports a failed build. Do not use that older project.

`frontend/vercel.json` sends same-origin `/api/v1/*` requests to the Railway staging FastAPI URL; the React client uses `/api/v1` for hosted builds by default when `VITE_API_BASE_URL` is unset. Local development still defaults to `http://localhost:8000/api/v1`. The proxy avoids cross-origin requests from the Vercel browser but **does not remove backend authentication**. Keep JWT verification and mission-grant checks enabled.

For the active Vercel project, set the following **public browser-build variables** under Settings → Environment Variables (Preview only while testing):

```dotenv
VITE_DATA_MODE=api
VITE_API_BASE_URL=/api/v1
VITE_SUPABASE_URL=https://ziecxjoeljxoocixejtz.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=<your public sb_publishable key>
```

Then redeploy the integration branch preview. No `NEXT_PUBLIC_` variables are consumed by this Vite app. Do not use `VITE_DATA_MODE=api` in Production until the authorized-user flow and seven dashboards have been reviewed. Without environment variables, the frontend intentionally remains in deterministic demo mode, even when the proxy is present.

The Vercel app integration was reported installed by the user but its account-management actions were not available to the assistant in that session, so these dashboard settings have **not** been remotely applied or verified.

## Credentials: do NOT paste secrets into GitHub code, chat, commits, or Vite variables

Frontend Vercel project (Root Directory `frontend`, Vite, output `dist`):
```dotenv
VITE_DATA_MODE=api
VITE_API_BASE_URL=https://YOUR-BACKEND-HTTPS-DOMAIN/api/v1
VITE_SUPABASE_URL=https://ziecxjoeljxoocixejtz.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=YOUR_PUBLIC_SUPABASE_PUBLISHABLE_KEY
```
`VITE_` variables are published to browser builds; use ONLY public Supabase keys. Do not use `NEXT_PUBLIC_` in this Vite project: that prefix is for Next.js. The frontend accepts `VITE_SUPABASE_PUBLISHABLE_KEY` or its legacy fallback `VITE_SUPABASE_ANON_KEY`. In the backend, the existing `SUPABASE_ANON_KEY` configuration can hold a publishable key because it is sent as an `apikey` header, not as a bearer JWT.

**Confirmed TeamRocket Supabase project:** `ziecxjoeljxoocixejtz` (project URL `https://ziecxjoeljxoocixejtz.supabase.co`). The repository's historical `docs/database/schema_handoff.json` names a different project reference, `ziecxjoelixoocixejtz`. **Do not treat that historical handoff as evidence that the confirmed project has the claimed 63 tables, migrations, permissions, or live RPC.** Inspect the confirmed project independently with `supabase/queries/integration_preflight.sql`, and only then reconcile or apply reviewed migrations. No keys are stored in this document. For an initial Vercel demo leave `VITE_DATA_MODE=demo`, without backend credentials.

Backend persistent host (Dockerfile at `backend/Dockerfile`, **build context repository root**; persistent mount at `/data`):
```dotenv
APP_ENV=development
SQLITE_PATH=/data/offline.db
DEV2_DATABASE_URL=sqlite:////data/dev2_clinical.db
LOCAL_ENCRYPTION_KEY=GENERATE_EXTERNALLY_AND_STORE_AS_SECRET
OFFLINE_GRANT_SECRET=GENERATE_32PLUS_RANDOM_CHARS_EXTERNALLY
AUTH_ISSUER=https://ziecxjoeljxoocixejtz.supabase.co/auth/v1
AUTH_JWKS_URL=https://ziecxjoeljxoocixejtz.supabase.co/auth/v1/.well-known/jwks.json
AUTH_AUDIENCE=authenticated
CORS_ORIGINS=https://YOUR-VERCEL-DOMAIN.vercel.app
SUPABASE_URL=https://ziecxjoeljxoocixejtz.supabase.co
SUPABASE_ANON_KEY=YOUR_PUBLIC_SUPABASE_PUBLISHABLE_OR_LEGACY_ANON_KEY
```
`LOCAL_ENCRYPTION_KEY` must be a Fernet-compatible key generated with
`python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.
A stable key and volume are essential: replacing them loses access to encrypted records. Never use `APP_ENV=production` with development auth/fixtures. Do not set `DEV_AUTH_SECRET` or `ALLOW_DEMO_RULES=true` in production.

Optional cloud sync additionally requires `SYNC_RPC_URL` and a short-lived **user** JWT `SYNC_ACCESS_TOKEN`. The current background worker does not refresh the JWT automatically; configure credential refresh or disable sync until a reviewed solution exists. A Supabase service-role key is NOT needed by this frontend adapter and should not be given to it. No migrations are applied automatically.

## Required Supabase project setup

The current Supabase connector account has no access to the confirmed TeamRocket project. A user-executed read-only SQL report previously showed 65 public tables with RLS enabled and the expected RPC, but not whether `anon` has `EXECUTE` on its `SECURITY DEFINER` function or whether live JWTs satisfy the RPC's membership checks. Run `supabase/queries/sync_security_preflight.sql` in the **correct project** to inspect permissions before enabling writes. Do not apply schema/permission mutations based on table counts alone.

1. Provision Supabase Auth users and server-controlled `app_metadata.roles` using one of `admin`, `flight_surgeon`, `crew`, `mission_control`, or `researcher`, and `app_metadata.mission_ids` such as `["DEMO-01"]`. `user_metadata` is NOT trusted for permission grants.
2. Verify that your project's token signing algorithm and published JWKS are compatible with FastAPI's existing JWT validation (RS256/ES256). A legacy HS256 project needs a reviewed auth strategy; this code does not accept that mode in online auth.
3. Complete baseline migrations and RLS reconciliation in an **empty development project** before enabling cloud sync. `supabase/README.md` documents missing prerequisites; the source tree is not a reproducible 57-table baseline.
4. Verify mission membership, sync receipts, idempotent replay, restart durability and negative permission tests. All clinical readouts must remain clearly labeled synthetic/research prototype.

## Smoke test
- Start the FastAPI container on a host with a durable mounted `/data` volume.
- GET `/api/health` returns an unauthenticated health status.
- GET `/openapi.json` lists `/api/v1/missions/{mission_id}/command`, `/api/v1/measurements/trends`, and `/api/v1/sync/status`.
- GET a protected endpoint without a Bearer token must return 401.
- Sign in as an authorized Supabase test user through the Vercel UI; the same account must have signed server-controlled app_metadata roles and mission grants.
- Add synthetic fixtures using reviewed seed commands or create records through authenticated endpoints; empty database returns empty/no-data UI, not fabricated live data.
- Verify the case/symptom workflow and acknowledgement with authorized flight-surgeon/admin account; unauthorized roles must receive 403.
- Run `cd backend && python -m unittest tests.test_frontend_api_adapter -v` and `cd frontend && npm ci && npm run build`.
- Never send real astronaut/patient data through this prototype.

## Outstanding gates
- Existing backend suite had documented failures before this branch; rerun all existing tests and resolve individually.
- Seeded Dev2 data resides in a distinct local SQLite database and does not establish authoritative cloud sync.
- Alert acknowledgement is handled in the compatibility adapter and requires careful clinical workflow/security review before any production claim.
- Domain records are intentionally partial; 57-table mapping and clinical validation remain incomplete.
- The default-branch README's Vercel `main` instructions are stale if `main` does not exist; select the correct branch explicitly.
