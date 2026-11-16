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

The verified active Vercel project is [teamrocket-rocketpulse](https://vercel.com/laymmmzs-projects/teamrocket-rocketpulse), created in the authorized `laymmmzs-projects` workspace and linked to `LAYMmMz/TeamRocket` with Root Directory `frontend` (Vite, Node 24, `npm ci`, `npm run build`, `dist`). Historical GitHub reports mentioned other Vercel projects, but those are **not present in the currently connected Vercel workspace**. Use the new project linked above, not an older 404 URL.

`frontend/vercel.json` sends same-origin `/api/v1/*` requests to the Railway staging FastAPI URL; the React client uses `/api/v1` for hosted builds by default when `VITE_API_BASE_URL` is unset. Local development still defaults to `http://localhost:8000/api/v1`. The proxy avoids cross-origin requests from the Vercel browser but **does not remove backend authentication**. Keep JWT verification and mission-grant checks enabled.

The following **public browser-build variables** have been configured through the Vercel API on **Preview only**, scoped to branch `feat/frontend-backend-api-integration`:

```dotenv
VITE_DATA_MODE=api
VITE_API_BASE_URL=/api/v1
VITE_SUPABASE_URL=https://ziecxjoeljxoocixejtz.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=<your public sb_publishable key>
```

The Preview deployment was created and reached `READY` for integration commit `235ab2a7e75bb38e3ddcaee01f0974ca01b52622`. Its URL is `https://teamrocket-rocketpulse-j8b3yead5-laymmmzs-projects.vercel.app`. A real fetch to Preview `/` returned HTTP 200. The same-origin Vercel rewrite `/api/health` returned HTTP 200 JSON from Railway: `environment=test`, `local_schema_version=2`, `cloud_sync_configured=false`. An authenticated API request was not verified without a valid authorized test user JWT. Production remains on Vite `demo` mode. No `NEXT_PUBLIC_` variables are consumed by this Vite app. Do not use `VITE_DATA_MODE=api` in Production until the authorized-user flow and seven dashboards have been reviewed. Without environment variables, the frontend intentionally remains in deterministic demo mode, even when the proxy is present.

Vercel team access was authorized in a later session. Project creation, environment variable settings, and Preview deployment were successfully completed and verified through the Vercel integration.

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

## No-connector Supabase verification and manual sync

The user can access the correct Supabase SQL Editor even though the ChatGPT Supabase connector cannot list that project. **Do not rerun migrations, edit policies, or expose secret keys to work around connector access.**

1. In Supabase → `TeamRocketV2Database` → SQL Editor → **New query**, copy only the contents of `supabase/queries/live_sync_preflight.sql` and press Run. It is one read-only SELECT returning `teamrocket_live_sync_preflight`.
2. Confirm the RPC has `security_definer=true`, `anon_can_execute=false`, `authenticated_can_execute=true`, a controlled `search_path`, and no public policies exposing data. Check for at least one eligible `DEMO-01` mission member. Independently review each policy.
3. Create a **synthetic/test** Supabase Auth user via the Supabase dashboard. Configure the backend-trusted `app_metadata.roles` (`admin` or `flight_surgeon`) and `app_metadata.mission_ids` (`["DEMO-01"]`) using a secure administrative workflow, not browser `user_metadata`. Ensure the same user has a row in `public.mission_members` for `DEMO-01`. Never paste the password or access token in chat.
4. Once RPC grants, JWT signing algorithm, and mission membership pass review, set **only** the following on the *Railway staging backend*: `SYNC_RPC_URL=https://ziecxjoeljxoocixejtz.supabase.co/rest/v1/rpc/ingest_sync_event`. Keep `SYNC_ACCESS_TOKEN` empty. A stable user JWT is not needed for **manual sync**; the endpoint `POST /api/v1/sync/run?mission_id=DEMO-01` uses a verified, live, short-lived Bearer session from the caller and requires `sync:manage` permission. A CLI/API client must explicitly send that session; the React UI currently does not provide a sync button. The endpoint never stores tokens.
5. Send **synthetic only** records through authorized FastAPI endpoints. Trigger manual sync, check the result, then **read** the exact event ID from Supabase `sync_receipts` and the destination `health_logs`/`clinical_records`. A 200 from `/api/health` is **not** proof of cloud synchronization; a matching receipt is.
6. Keep the integration preview gated by Supabase Auth. Public judge access can remain `VITE_DATA_MODE=demo` until a separately reviewed, anonymous **read-only synthetic** endpoint exists.

The backend health endpoint reports `cloud_sync_configured` for the older automatic worker (requires a stored JWT), and `manual_cloud_sync_configured` for the new manual user-session path (requires an RPC URL and public key). Both settings describe **configuration**, not verified remote writes.

**Known risk:** The repository's earlier migration `supabase/migrations/20261115_02_ingest_sync_event_rpc.sql` has an old unguarded seed snippet involving `v_demo_user_id`; do not rerun historical SQL against the existing database. Review the deployed RPC `pg_get_functiondef` and grants instead if the preflight indicates a mismatch.


## Security audit finding (2026-11-16, confirmed through user's SQL Editor)

**Do NOT enable the Railway `SYNC_RPC_URL` yet.** The live `TeamRocketV2Database` read-only audit returned:

- `public.ingest_sync_event(jsonb)`: `SECURITY DEFINER=true`, function owner `postgres`, `anon_can_execute=true`, `authenticated_can_execute=true`, `search_path=public`. Anonymous function access must be revoked even though the RPC checks `auth.uid()` internally.
- `public.health_logs`: a policy named `Enable all access for hackathon on health_logs` allows `ALL TO public USING (true) WITH CHECK (true)`. It overrides the otherwise present `health_logs_read_mission_members` policy for applicable roles.
- `public.missions`: RLS enabled but no policies; non-privileged direct reads are denied. Do not add an unrestricted read policy.
- 7/7 required tables with RLS enabled, `DEMO-01` has three mission_members, six astronauts, and five existing sync receipts. Table counts are not proof of correct permissions or end-to-end data flow.

The reviewed, *manually executed* narrow remediation is `supabase/manual/20261116_restrict_sync_rpc_and_health_logs.sql`. It atomically revokes `PUBLIC` and `anon` execution on the privileged RPC, retains `authenticated` execution, drops the exact broad health_logs policy, preserves the mission-scoped SELECT policy, and removes anonymous table access. It contains a precondition guard and a verification SELECT. It **has not been run** in Supabase because ChatGPT's connector cannot access this project.

**Owner action:** open the correct Supabase SQL Editor, review and execute that SQL file, then share only the final verification row. Expected `anon_rpc_execute=false`, `authenticated_rpc_execute=true`, `anon_health_logs_select_grant=false`, `unrestricted_policy_present=false`, and `mission_policy_present=true`. If execution fails, stop and share the error; do not run arbitrary grants or legacy migrations. After validation, verify authorized JWT claims and mission membership, configure Railway's fixed `SYNC_RPC_URL` for the on-demand user-session sync route, then match the exact synthetic event receipt in `public.sync_receipts`.


## Automatic synchronization (authenticated browser session; enabled in integration preview)

- RocketPulse Preview's API-mode frontend mounts `AutoSyncProvider` globally. A signed-in authorized user triggers `POST /api/v1/sync/run?mission_id=DEMO-01` automatically after login and once every **45 seconds** while the dashboard remains open. The Integration page displays the session's confirmed delivery count, failed attempts, queue size and last matching receipt timestamp, and provides a manual "Sync now" button.
- Backend checks `sync:manage`, mission authorization, and an asymmetric-signed verified Supabase access JWT. No access token is saved to Railway. A user with role `crew` should see the sync as **blocked**; a mission-scoped `admin`, `flight_surgeon` or `mission_control` user is authorized to attempt syncing, subject to the live JWT claims.
- The worker selects only event kinds supported by Supabase `ingest_sync_event(jsonb)`; unsupported outbox events (for example, standalone `audit`) remain in local SQLite rather than exhausting retries. The existing RPC validates `auth.uid()` and membership in `public.mission_members`.
- GitHub Actions tests exercise backend authorization, synthetic measurement → queue → matching receipt through a **local memory transport**, unsupported event filtering and the frontend build. **Passing tests does not prove live cloud delivery.**
- **Important**: This is *session-based automatic synchronization*, not unattended 24/7 server-background synchronization. Closing all authorized browser sessions stops periodic triggers. A true always-on headless worker would need a separately reviewed dedicated service identity, refresh/rotation plan, and Supabase permissions. Do not set `SYNC_ACCESS_TOKEN` to a captured personal JWT to fake a permanent worker; it expires and creates credential-handling risks.
- To verify a live delivery: sign into the Preview with an authorized synthetic test account; create a synthetic measurement via the authenticated API; in the Integration dashboard wait for `CONFIRMED THIS SESSION` to increase; compare the precise remote event ID (typically `measurement:<event_id>`) with a Supabase read-only `sync_receipts` SELECT. If the account uses an HS256-only legacy JWT signing configuration, the current API will deny cloud sync; do not disable signature validation to work around it.
- If the server has the RPC URL and public key, `manual_cloud_sync_configured=true` in `/api/health`. The older `cloud_sync_configured` reflects the disabled fixed-token background worker. The two flags are intentionally distinct.

