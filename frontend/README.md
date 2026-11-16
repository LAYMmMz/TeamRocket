# RocketPulse V2 — Vortex Spacecraft Command Edition

**The React frontend for TeamRocket's RocketPulse synthetic-data research prototype**, mapped to the **NASA Astronaut Health Monitoring — Final Development MasterDocs (15 November 2026)**. The visual style is **inspired by** [Imran Jakir's Futuristic Spacecraft Command Dashboard](https://dribbble.com/shots/27171089-Futuristic-Spacecraft-Command-Dashboard-Sci-Fi-Spaceship-UI), adapted into an original medical mission-control interface. No designer assets were copied.

## What is included

- 7 PDF-specific role-oriented dashboard views (F40–F46), **all navigable**; navigability is not full workflow acceptance.
- 12 monitoring-domain pages with clinical caution text and canonical table references. Only domains with published approved synthetic samples return records; other domains display unavailable/empty states.
- 47-feature searchable traceability board, each feature discoverable at `/features/F01` ... `/features/F47`. Feature pages document available reads and acceptance gaps; they do not mean all 47 clinical workflows are implemented.
- 57 exact logical cloud tables and starter columns; 6 physical SQLite tables documented and browsable. The Schema-Aware Data Intake page generates browser-side synthetic JSON drafts for any canonical cloud table (never direct DB writes).
- All 12 scenario IDs S01–S12, five hazards and eight research-gap categories.
- 3D astronaut prototype with clickable head/chest/torso/arms/legs and alternative controls.
- Deterministic 30-day, four-crew browser fixtures (8,640 HR/SpO2/RR plus 240 systolic BP readings) are available **only in explicit demo mode**; scenario changes do not execute backend acceptance tests.
- Medical alert review, acknowledgement and symptom form. In **demo mode** these are **browser-only**, not authoritative clinical events.
- Frontend module switchboard and shared reading metadata (units, provenance, quality, verification, timestamps, synthetic labels).
- Centralized FastAPI fetch client, typed contracts, a public GET-only approved-synthetic feed, and protected JWT-required API operations.

**Not claimed:** complete acceptance of all 47 features, a full bootstrap of all 57 cloud tables, complete clinical-domain datasets, validated medical rules or procedures, deployed end-to-end authorization for every workflow, or NASA operational/medical-device certification. See the [PDF alignment and acceptance blockers](../docs/PDF_ALIGNMENT_STATUS.md) and [QA scope](docs/QA_AND_SCOPE.md).

## Windows setup (PowerShell, including machines with npm PATH issues)

1. Install Node.js LTS from <https://nodejs.org/en/download> with npm and PATH enabled.
2. Restart VS Code after installing.
3. Open the folder containing **this** `package.json`.
4. Run:

```powershell
node -v
npm.cmd -v
npm.cmd ci
Copy-Item .env.example .env
npm.cmd run dev
```

Open the URL Vite prints (usually <http://localhost:5173>). If `npm.cmd` is not recognized, fix Node.js installation/PATH before attempting any project troubleshooting.

For macOS/Linux, use `npm ci`, `cp .env.example .env`, then `npm run dev`.

## Modes and backend integration

The app defaults to **public mode**. It reads only approved synthetic sample records through the FastAPI `/api/v1/public` GET endpoints; it does not read protected clinical tables or write data. Missing records and request failures stay unavailable—there is no fixture fallback.

```ini
VITE_DATA_MODE=public
VITE_API_BASE_URL=/api/v1
```

Use **demo mode** only to explore deterministic browser fixtures and UI scenarios; demo writes stay in the browser and are not clinical records:

```ini
VITE_DATA_MODE=demo
```

**API mode** calls protected FastAPI endpoints and requires a valid user access token. The frontend obtains it through the Supabase Auth provider; FastAPI must enforce mission and record authorization for every request. Never expose a service-role key in the browser. API failures are shown and never cause a switch to demo fixtures.

For local public/API reads, start FastAPI on port `8000`; Vite proxies `/api` to it. Hosted Vercel uses the same-origin rewrite configured in `vercel.json`. Browser `VITE_*` variables are public and must contain no database password or service-role key.

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
npm.cmd run test:database-ui
```

The scope test uses Node's built-in filesystem and can run without installed npm packages (`node scripts/check-scope.mjs`). `test:database-ui` uses Playwright with controlled API responses; install Chromium once with `npx playwright install chromium`. It verifies frontend behavior, not live Supabase permissions or clinical acceptance.

## Demo walkthrough

1. Open `/command` and select a synthetic crew identifier. Readings and trends come from the approved public FastAPI feed, not the browser fixture generator.
2. Rotate the 3D astronaut, select a body area, and open the linked health domain. The model is a navigation aid, not a medical scan.
3. Open `/cases`; protected writes and alert acknowledgments are unavailable in public mode.
4. Open `/simulation`. Outside explicit demo mode, scenarios are reference descriptions, not backend executions.
5. Open `/data-model` and inspect the logical cloud catalog; it is not a live schema inspection.
6. Open `/coverage` to review the 47 traceability entries and their incomplete acceptance status.

## Safety

This is **a synthetic-data research prototype, not NASA-certified software or medical guidance**. It does not provide diagnosis, treatment, EVA clearance, or spacecraft actuation. Research-only rules and unapproved/expired procedures are not operational medical guidance. Backend is responsible for local SQLite commit-first operation, secure offline grants, approved versioned rules, record-level authorization, append-only audit, idempotent sync and Supabase RLS.
