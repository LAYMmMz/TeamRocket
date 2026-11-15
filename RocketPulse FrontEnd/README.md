# RocketPulse V2 — Vortex Spacecraft Command Edition

**A real, modular React frontend starter** built around the user's **NASA Astronaut Health Monitoring — Final Development MasterDocs (15 November 2026)**. The visual style is **inspired by** [Imran Jakir's Futuristic Spacecraft Command Dashboard](https://dribbble.com/shots/27171089-Futuristic-Spacecraft-Command-Dashboard-Sci-Fi-Spaceship-UI), adapted into an original medical mission-control interface. No designer assets were copied.

## What is included

- 7 PDF-specific role-oriented dashboards (F40–F46), **all navigable**.
- 12 monitoring domains with clinical caution text, sample records and canonical table references.
- 47-feature searchable traceability board, each feature with its own detail URL (`/features/F01` ... `/features/F47`).
- 57 exact logical cloud tables and starter columns; 6 physical SQLite tables documented and browsable. The Schema-Aware Data Intake page generates browser-side synthetic JSON drafts for any canonical cloud table (never direct DB writes).
- All 12 scenario IDs S01–S12, five hazards and eight research-gap categories.
- 3D astronaut prototype with clickable head/chest/torso/arms/legs and alternative controls.
- Synthetic 30-day, 4-crew **vital readings** generated deterministically (8,640 HR/SpO2/RR plus 240 systolic BP sample records); scenario fixture changes.
- Medical alert review, acknowledgement and symptom form. In **demo mode** these are **browser-only**, not authoritative clinical events.
- Frontend module switchboard and shared reading metadata (units, provenance, quality, verification, timestamps, synthetic labels).
- Centralized FastAPI fetch client, typed contracts and proposed OpenAPI handoff.

**Not included / not claimed:** FastAPI server, all 57 real Supabase SQL migrations, SQLite engine or encryption, NASA dataset ingestion, real authentication/RLS, persistent clinical workflow, sync receipts, clinical validation, backend tests, authorized procedures, or a verified production build. The UI explicitly calls out these dependencies. The PDF requires them for complete acceptance.

## Windows setup (PowerShell, including machines with npm PATH issues)

1. Install Node.js LTS from <https://nodejs.org/en/download> with npm and PATH enabled.
2. Restart VS Code after installing.
3. Open the folder containing **this** `package.json`.
4. Run:

```powershell
node -v
npm.cmd -v
npm.cmd install
Copy-Item .env.example .env
npm.cmd run dev
```

Open the URL Vite prints (usually <http://localhost:5173>). If `npm.cmd` is not recognized, fix Node.js installation/PATH before attempting any project troubleshooting.

For macOS/Linux, use `npm install`, `cp .env.example .env`, then `npm run dev`.

## Modes and backend integration

The frontend defaults to clearly labeled deterministic synthetic fixtures:

```ini
VITE_DATA_MODE=demo
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

Switch to **API mode** only when your Python backend exposes the endpoints described in `docs/BACKEND_HANDOFF.md`:

```ini
VITE_DATA_MODE=api
```

In API mode, backend failure is shown as an error; the app does not silently populate mock NASA readings. Supply a Supabase Auth token provider using `configureAuthTokenProvider` in `src/lib/api.ts`; never expose service-role keys in React. The backend must authorize all operations and enforce record access.

## How to add/remove UI modules

Open **Module Switchboard** in the sidebar. Toggle nav visibility for each route; preference is saved in this browser. For permanent code-level changes, edit the `modules` registry in `src/App.tsx`. To add a new feature, create its component in `src/pages`, register a route and module entry, and add the relevant typed API method. Do **not** create duplicate Supabase tables for screens; reuse the 57 canonical sources.

## How to adjust design

`src/styles.css` contains theme tokens at the top. Main colors: `#07080A` space black; `#304E58` steel cyan; `#A68D6F` warm khaki; `#AF4E27` amber/burnt orange; `#C7BFAF` warm text. The astronaut is procedural Three.js geometry in `src/components/AstronautScene.tsx`. Replace it with a licensed GLB later, retaining the `region` and `onChange` interface.

## Folder guide

- `src/data/masterdocs.json` — single frontend-readable specification of domains, views, features, tables, hazards, scenarios, and API groups.
- `src/lib/types.ts` — typed contracts with provenance and synthetic labels.
- `src/lib/demo.ts` — deterministic synthetic dataset and scenario fixtures (NOT clinical thresholds).
- `src/lib/api.ts` — backend integration adapter.
- `src/pages/Dashboards.tsx` — seven dashboards and 3D Body Explorer.
- `src/pages/Operations.tsx` — domains, incidents, 12 scenarios, database, and architecture.
- `src/pages/Traceability.tsx` — 47 feature details and source research register.
- `src/pages/DataIntake.tsx` — field-driven synthetic JSON draft workbench for all 57 PostgreSQL tables (no persistence).
- `src/app/MissionContext.tsx` — crew, scenario, roles for UI preview, module toggles.
- `src/styles.css` — responsive Vortex-inspired look.
- `docs/FEATURE_MATRIX.md` — 47 feature requirement crosswalk.
- `docs/DATABASE_MAP.md` — canonical SQL table/field inventory and offline mappings.
- `docs/BACKEND_HANDOFF.md` — proposed API methods, Pydantic schema examples and clinical safeguards.
- `docs/QA_AND_SCOPE.md` — what has and has not been verified.

## Run scope manifest checks

```powershell
npm.cmd run check:scope
npm.cmd run typecheck
npm.cmd run build
```

The scope test uses Node's built-in filesystem and can run without installed npm packages (`node scripts/check-scope.mjs`). The TypeScript build requires `npm install` and network access to the npm registry.

## Demo walkthrough

1. Open `/command` and choose **S04** to show evidence-linked CO2 / headache alert.
2. Rotate the 3D astronaut and select **chest**, then open its monitoring domain.
3. Open `/cases` and acknowledge the simulated incident (browser-only state).
4. Open `/simulation`, switch to S03 and confirm SpO₂ is **missing**, not falsely displayed as normal.
5. Open S10 to see the simulated connection-loss UI (not actual SQLite sync).
6. Open `/data-model` and inspect 57 canonical cloud tables / six SQLite tables.
7. Open `/coverage` and show all 47 feature IDs plus the seven role dashboards.

## Safety

This is **a synthetic-data research prototype, not NASA-certified software or medical guidance**. It does not provide diagnosis, treatment, EVA clearance, or spacecraft actuation. Research-only rules and unapproved/expired procedures are not operational medical guidance. Backend is responsible for local SQLite commit-first operation, secure offline grants, approved versioned rules, record-level authorization, append-only audit, idempotent sync and Supabase RLS.
