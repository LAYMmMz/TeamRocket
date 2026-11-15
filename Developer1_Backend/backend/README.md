# TeamRocket Backend — Run Guide

FastAPI backend for the TeamRocket astronaut health-monitoring **synthetic-data prototype**. The backend includes Dev 1's encrypted local SQLite store and sync queue, plus Dev 2 clinical/demo endpoints backed by a separate local SQLite database.

> Run these commands from `Developer1_Backend/backend`, not the Git repository root. The examples use **Windows PowerShell** and Python **3.13**, which has been used for local testing. This is not a production deployment guide.

## 1. Get started

In VS Code, open a PowerShell terminal at the TeamRocket repository root:

```powershell
cd Developer1_Backend/backend
py -3.13 --version
py -3.13 -m pip install -r requirements.txt
py -3.13 -m pip install sqlalchemy
```

The current `requirements.txt` lists the core FastAPI dependencies; the integrated Dev 2 clinical models additionally import SQLAlchemy. No virtual environment is required, but you can use one if you prefer.

Start the API:

```powershell
py -3.13 dev.py
```

On first run, `dev.py` creates a local `.env` if none exists, with development authentication secrets. It loads existing values from `.env` without overriding variables already set in the terminal. It then prints a **development-only API token**.

Open:

- Swagger UI: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/api/health
- OpenAPI schema: http://127.0.0.1:8000/openapi.json

In Swagger, select **Authorize** and paste the **development token printed by `dev.py`** (without `Bearer ` if the Swagger dialog already adds it). Keep the server terminal open; use **Ctrl+C** to stop it.

## 2. Configure Supabase cloud synchronization (optional)

**Offline/local development works without Supabase.** To enable cloud delivery, you need an existing Supabase project with the Database Team's `public.ingest_sync_event(p_event JSONB)` RPC migration, an authenticated test user, and permission to access the target mission (for example, `DEMO-02`).

Add your project's settings to `Developer1_Backend/backend/.env`:

```dotenv
APP_ENV=development
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_ANON_KEY=YOUR_PUBLISHABLE_OR_ANON_KEY
AUTH_ISSUER=https://YOUR_PROJECT.supabase.co/auth/v1
AUTH_JWKS_URL=https://YOUR_PROJECT.supabase.co/auth/v1/.well-known/jwks.json
AUTH_AUDIENCE=authenticated
CORS_ORIGINS=http://localhost:5173
```

Do not replace an existing `DEV_AUTH_SECRET` or `OFFLINE_GRANT_SECRET` with blank values. Use a **publishable/anon** key for `SUPABASE_ANON_KEY`, never a Supabase secret/service-role key.

For cloud sync, the server process needs both:

- `SYNC_RPC_URL=https://YOUR_PROJECT.supabase.co/rest/v1/rpc/ingest_sync_event`
- `SYNC_ACCESS_TOKEN`, an authenticated Supabase **user access JWT** for an authorized mission member

The repository contains a helper to obtain the test user's JWT. **Stop the backend first**, then use the **same PowerShell terminal in which you will start the server**:

```powershell
# Run from Developer1_Backend/backend
# Load .env into this terminal (the login helper reads process environment variables).
Get-Content .env | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith("#") -and
        $line -match '^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
        [Environment]::SetEnvironmentVariable(
            $matches[1],
            $matches[2].Trim().Trim('"').Trim("'"),
            "Process"
        )
    }
}

& "..\TeamRocket_Unified_Cloud_Patch_V2\login_supabase_test.ps1" -Email "YOUR_TEST_USER_EMAIL"
py -3.13 dev.py
```

The helper requests the test user's password without displaying it, sets `SYNC_ACCESS_TOKEN` and `SYNC_RPC_URL` **in that terminal only**, and does not print the access token. If PowerShell blocks the script, you can first run `Set-ExecutionPolicy -Scope Process Bypass` in that terminal (only if you trust the local script). Do **not** paste JWTs into GitHub or chat.

Verify from a **second terminal**:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

With a configured server, `cloud_sync_configured` should be `True`. When the user JWT expires, stop the server, rerun the login helper, and restart it. The **local development API token** printed by `dev.py` and the **Supabase cloud-sync JWT** serve different purposes; one cannot simply replace the other.

## 3. Try the API

Use Swagger at `/docs` to explore the endpoints. Typical routes include:

| Route | Purpose |
| --- | --- |
| `GET /api/health` | Check service and cloud configuration |
| `POST /api/measurements` | Ingest a vital measurement with provenance |
| `GET /api/measurements` | List measurements by mission |
| `POST /api/symptoms` | Create a synthetic Dev 2 symptom report |
| `POST /api/sync/run` | Trigger a Dev 1 cloud sync cycle |
| `GET /api/sync/status` | View pending, synced, retry and dead queue counts |

Except for the health check, these routes require the appropriate authenticated API role and mission permissions. The development token printed by `dev.py` has an admin role for demo missions `DEMO-01` and `DEMO-02`.

Use **fictional/synthetic data only**. Do not treat simulated alerts, scenarios, or clinical records as medical guidance.

## 4. Run tests

From `Developer1_Backend/backend`:

```powershell
py -3.13 run_teamrocket_tests.py
```

This runs the available local unittest suite with disposable encrypted SQLite storage and writes `teamrocket_test_report.json`. Check **FAIL**, **ERROR**, and **BLOCKED** separately. The acceptance runner documents incomplete S04/S05 scenario workflows; passing executable tests does **not** mean every S01–S12 clinical scenario has been verified.

The optional `run_final.py` checks live FastAPI/Supabase connectivity if configured. It may prompt for a Supabase test-user login and create synthetic cloud records:

```powershell
py -3.13 run_final.py
```

Do not use this against production or real patient data. A successful sync-worker count does not, by itself, prove a particular event was delivered: match its exact event ID to Supabase `sync_receipts` and, for clinical events, `clinical_records`.

## 5. Troubleshooting

| Problem | What to check |
| --- | --- |
| `Unable to connect to remote server` | Run `py -3.13 dev.py` and keep the server terminal open; confirm port 8000 |
| `cloud_sync_configured=False` | The **server** was started without `SYNC_RPC_URL` or `SYNC_ACCESS_TOKEN`; log in and restart from the same terminal |
| `Development token issuance is disabled` | `APP_ENV` must be `development` or `test` and `DEV_AUTH_SECRET` must be set (at least 32 characters) |
| `authentication_required` | Supply the local API Bearer token via Swagger or the HTTP `Authorization` header |
| Supabase 401/403 on sync | Refresh the Supabase test-user JWT and confirm the user belongs to the mission |
| `No module named 'sqlalchemy'` | Run `py -3.13 -m pip install sqlalchemy` |
| Queue shows `dead` entries | These may be older failures; inspect them instead of deleting offline data |
| The API works locally but no symptom receipt appears | Verify the installed Dev 2 bridge actually enqueues `symptom` into Dev 1's queue, then match the exact cloud event ID |

## 6. Security and scope

- Never commit `.env`, `.env.local`, JWTs, secret keys, local `*.db` files, `*.key` files, `.venv/`, or generated test reports.
- This repository contains **prototype** clinical features. Not all Dev 2 modules are proven to synchronize to Supabase.
- Production requires independent security review, reviewed clinical rules, proper RLS/mission access, HTTPS authentication, and externally managed secrets and encryption keys.
- The local database and cloud destination are different; don't assume a locally saved event has reached Supabase until its specific receipt is verified.
