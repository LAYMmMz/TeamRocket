# TeamRocket — RocketPulse

Astronaut health monitoring frontend prototype using React, TypeScript and Vite.

## Repository layout

| Path | Purpose |
| --- | --- |
| `frontend/` | Complete Vite application, including package.json, its dependency lockfile, configuration, source, assets and scripts |
| `frontend/docs/` | API handoff, database map, feature matrix and QA notes |
| `database/docs/DatabaseSchema.md` | Existing database design proposal; not an executable migration |
| `backend/` (future) | Add the actual FastAPI application, dependencies and tests here when implemented |
| `database/migrations/` (future) | Add reviewed SQL migrations here when implemented |

There is currently no backend implementation or executable SQL migration in this repository. Creating folders does not connect a database.

## Run locally (Windows PowerShell)

From the repository directory:

```powershell
cd frontend
npm.cmd ci
Copy-Item .env.example .env
npm.cmd run dev
```

Copy the environment template only on first setup; preserve an existing local .env. Use a Node.js release compatible with the locked Vite version. On macOS/Linux use npm and cp.

## Validate

Run from frontend:

```powershell
npm.cmd run check:scope
npm.cmd run typecheck
npm.cmd run build
```

## Vercel configuration after merging this reorganization

If an existing Vercel project points to `RocketPulse FrontEnd`, change its Root Directory to `frontend` when deploying this branch. The previous folder path no longer exists in this layout.

- Root Directory: `frontend`
- Framework: Vite
- Install Command: `npm ci`
- Build Command: `npm run build`
- Output Directory: `dist`

Keep `vercel.json` inside frontend. It contains the SPA route fallback. Validate a preview deployment before switching production.

For the current synthetic demo, use `VITE_DATA_MODE=demo`. When the backend is ready, configure `VITE_DATA_MODE=api` and `VITE_API_BASE_URL` to its HTTPS API URL ending in `/api/v1`, then redeploy. Implement the API contract and authentication described in [the backend handoff](frontend/docs/BACKEND_HANDOFF.md). The backend must allow the frontend origin through its CORS configuration.

Vite browser variables are public. Keep database credentials and Supabase service-role keys on the backend.

## Database document reconciliation

[DatabaseSchema.md](database/docs/DatabaseSchema.md) is preserved as supplied. It describes Next.js and NEXT_PUBLIC_* variables, but the actual frontend is Vite and uses VITE_* variables. It also names some tables differently from [DATABASE_MAP.md](frontend/docs/DATABASE_MAP.md), including health_logs versus vital_signs and incidents versus medical_incidents. Reconcile these proposals with the project requirements before implementing migrations. Do not treat the schema proposal as proof that a database is deployed.

## Cleanup decisions

- Removed the old repository-root `package-lock.json`: its packages object was empty and there was no root package.json.
- Keep `frontend/package-lock.json`: it is the application's dependency lockfile.
- The old `RocketPulse FrontEnd/` directory was moved intact to `frontend/`; do not upload a second copy.
- Keep source files, public assets, configuration, .env.example and the documentation.
- `frontend/preview.html` is a standalone preview, not the Vite index.html entry point. It is retained; removing it is optional if the team no longer needs it.
- Keep `frontend/scripts/generate-spec.py` for now. It currently contains an old absolute output path; update that path before using it. This reorganization does not run it.
- node_modules, dist and local environment files should not be committed. A root .gitignore covers future backend work too.

See [the frontend README](frontend/README.md) for the detailed feature scope and demo walkthrough.
