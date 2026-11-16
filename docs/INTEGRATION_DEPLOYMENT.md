# RocketPulse frontend–backend integration (synthetic research prototype)

## Scope
This branch includes protected FastAPI `/api/v1` compatibility endpoints used by the active Vite dashboard, Supabase user login (not a service-role client), and a backend container recipe. It does not deploy your infrastructure, set up Supabase, validate the 57-table cloud schema, or pass the older backend's unresolved acceptance suite. Domain2 SQLite fixtures are exposed only for `APP_ENV=development/test` and `DEMO-01`, with synthetic flags. Production must not rely on those fixtures.

## Credentials: do NOT paste secrets into GitHub code, chat, commits, or Vite variables

Frontend Vercel project (Root Directory `frontend`, Vite, output `dist`):
```dotenv
VITE_DATA_MODE=api
VITE_API_BASE_URL=https://YOUR-BACKEND-HTTPS-DOMAIN/api/v1
VITE_SUPABASE_URL=https://YOUR-SUPABASE-PROJECT.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=YOUR_PUBLIC_SUPABASE_PUBLISHABLE_KEY
```
`VITE_` variables are published to browser builds; use ONLY public Supabase keys. Do not use `NEXT_PUBLIC_` in this Vite project: that prefix is for Next.js. The frontend accepts `VITE_SUPABASE_PUBLISHABLE_KEY` or its legacy fallback `VITE_SUPABASE_ANON_KEY`. In the backend, the existing `SUPABASE_ANON_KEY` configuration can hold a publishable key because it is sent as an `apikey` header, not as a bearer JWT.

**Project identification:** The checked-in `docs/database/schema_handoff.json` identifies project `ziecxjoelixoocixejtz`, whereas a later user-supplied URL identifies `ziecxjoeljxoocixejtz`. These are different Supabase project refs. Confirm the correct project in Supabase **Settings > General** before configuring any deployment or migrating data. This deployment guide intentionally contains placeholders rather than choosing one. For an initial Vercel demo leave `VITE_DATA_MODE=demo`, without backend credentials.

Backend persistent host (Dockerfile at `backend/Dockerfile`, **build context repository root**; persistent mount at `/data`):
```dotenv
APP_ENV=development
SQLITE_PATH=/data/offline.db
DEV2_DATABASE_URL=sqlite:////data/dev2_clinical.db
LOCAL_ENCRYPTION_KEY=GENERATE_EXTERNALLY_AND_STORE_AS_SECRET
OFFLINE_GRANT_SECRET=GENERATE_32PLUS_RANDOM_CHARS_EXTERNALLY
AUTH_ISSUER=https://YOUR-SUPABASE-PROJECT.supabase.co/auth/v1
AUTH_JWKS_URL=https://YOUR-SUPABASE-PROJECT.supabase.co/auth/v1/.well-known/jwks.json
AUTH_AUDIENCE=authenticated
CORS_ORIGINS=https://YOUR-VERCEL-DOMAIN.vercel.app
SUPABASE_URL=https://YOUR-SUPABASE-PROJECT.supabase.co
SUPABASE_ANON_KEY=YOUR_PUBLIC_SUPABASE_PUBLISHABLE_OR_LEGACY_ANON_KEY
```
`LOCAL_ENCRYPTION_KEY` must be a Fernet-compatible key generated with
`python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.
A stable key and volume are essential: replacing them loses access to encrypted records. Never use `APP_ENV=production` with development auth/fixtures. Do not set `DEV_AUTH_SECRET` or `ALLOW_DEMO_RULES=true` in production.

Optional cloud sync additionally requires `SYNC_RPC_URL` and a short-lived **user** JWT `SYNC_ACCESS_TOKEN`. The current background worker does not refresh the JWT automatically; configure credential refresh or disable sync until a reviewed solution exists. A Supabase service-role key is NOT needed by this frontend adapter and should not be given to it. No migrations are applied automatically.

## Required Supabase project setup
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
