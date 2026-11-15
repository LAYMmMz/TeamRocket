# TeamRocket — RocketPulse

Astronaut health-monitoring research prototype with synthetic data. This repository consolidates the team's frontend, backend and database branches. It is not NASA-certified software or a completed clinical system.

## Where each part belongs

| Directory | Contents |
| --- | --- |
| `frontend/` | Active RocketPulse React + TypeScript + Vite interface from main |
| `backend/` | Integrated Python/FastAPI application from the backend branch |
| `backend/offline/migrations/` | Local SQLite migration scripts used by the backend |
| `supabase/migrations/` | Database team's forward cloud RPC migrations; prerequisites are incomplete |
| `supabase/rollbacks/` | Manual rollback scripts, never run as forward migrations |
| `supabase/queries/` | Read-only schema inspection SQL |
| `supabase/legacy/` | Original partial schema for reference; not a deployment baseline |
| `docs/database/` | Database exports, mappings, contracts and teammate test notes |
| `docs/schema-handoff.json` | Backend's existing schema manifest |
| `database/docs/` | Original schema proposal, preserved for reconciliation |
| `archive/` | Alternative frontend, earlier database prototype and patch packages |

See [the consolidation record](docs/REPOSITORY_ORGANIZATION.md) for source branches and cleanup decisions. Use the active frontend for Vercel. Do not merge archived app files into it by filename: they have different contracts.

## Frontend: local setup

Use Node.js 24.x. From the repository root in PowerShell:

```powershell
cd frontend
npm.cmd ci
npm.cmd run check:scope
npm.cmd run build
npm.cmd run dev
```

Demo mode is the default. For explicit local configuration, copy `.env.example` to `.env` only if no local .env already exists. On macOS/Linux, use `npm` instead of `npm.cmd`.

## Vercel: deploy the frontend demo

Import `LAYMmMz/TeamRocket` and select:

| Setting | Value |
| --- | --- |
| Production branch | `main` |
| Framework | Vite |
| Root Directory | `frontend` |
| Install Command | `npm ci` |
| Build Command | `npm run build` |
| Output Directory | `dist` |
| Node.js | 24.x |
| Environment variable | `VITE_DATA_MODE=demo` |

For an existing project, change its Root Directory from `RocketPulse FrontEnd` to `frontend` before the next deployment. Keep `frontend/vercel.json` for SPA deep-link rewrites. Check all dashboards, assets and a direct refresh of `/command` after deployment.

## Backend: local setup

Use a separate terminal. The backend team used Python 3.13. From the repository root:

```powershell
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe dev.py
```

`dev.py` creates development secrets in a local .env on first run and prints a local development token. Do not commit that file or share the token. Open http://127.0.0.1:8000/docs and http://127.0.0.1:8000/api/health. Read [backend/README.md](backend/README.md) before enabling optional cloud sync.

Run local tests from backend:

```powershell
.\.venv\Scripts\python.exe run_teamrocket_tests.py
```

No live Supabase operations were authorized or performed as part of repository organization.

## Integration status

The active frontend expects `/api/v1` and proposed response shapes, while the backend exposes `/api` and its own contracts. Changing only VITE_API_BASE_URL is not sufficient. Authentication, endpoint/response mapping and demo-only sections must be reconciled before enabling `VITE_DATA_MODE=api`.

Vercel serves this frontend. The existing backend uses local SQLite files and a background sync worker, so it needs a runtime with durable local storage; this cleanup does not deploy or adapt it to serverless execution. The Supabase migration set is incomplete for a clean database: see [supabase/README.md](supabase/README.md). Do not run the SQL blindly.

The source manifest lists 47 features, 57 cloud tables, six offline tables and 12 scenarios. Inventory coverage is not evidence that all acceptance criteria pass.

## Working with branches

All five existing branches were included in the consolidation. The consolidation commit preserves their starting commits as parents. This layout is currently on the review branch; main and the original work branches have not been updated. Future changes belong in their component folders on feature branches, then into main through reviewed pull requests.

Historical alternatives are in archive for reference, not automatic deployment. Review this consolidation instead of merging the older layout proposals independently.

## Secrets and generated files

Local databases, the committed offline encryption key, .env.local, Python bytecode, duplicate empty files and obsolete backup copies were excluded from the consolidated tree. Their historical commits remain in Git. Treat the old offline key as exposed; replace it for any reused environment and re-encrypt retained data with an appropriate migration. Inspect historical environment configuration for any private credentials and rotate any that were real. Do not copy old local databases or keys back into the repository.

Git ignores local environment files, databases/keys, caches, dependencies, builds and generated test reports. Keep package-lock.json and .env.example files.

## Verification during consolidation

Frontend: npm ci, check:scope and production build passed on Node 24.22.1. Static image/model blobs were preserved by Git SHA; they were not copied into the local build workspace, so browser/asset rendering was not verified. Vite reported a large JavaScript chunk.

Backend: the local suite on Python 3.12 ran 151 checks: 123 PASS, 21 FAIL, 3 ERROR, 4 BLOCKED. The runtime application and test sources are preserved unchanged from the backend branch. Errors include missing reports `domains` response data; failures include authorization/response expectations. This is a repository cleanup, not completion of those integration fixes. No live Supabase/RLS or deployed-browser test was performed.
