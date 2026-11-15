# TeamRocket — Flight Health

React + TypeScript + Three.js frontend for the NASA Space Apps Challenge astronaut health monitoring prototype. The authoritative specification is the uploaded **Final Development MasterDocs, 15 November 2026 (13 pages)**. This is an independent synthetic-data prototype, not NASA flight software.

## Run now

1. Install Node.js 22 LTS (or a compatible maintained Node release) and Git.
2. Clone this repository and enter `frontend`.
3. Run `npm ci`.
4. Copy `.env.example` to `.env.local`. Keep `VITE_DATA_MODE=mock`.
5. Run `npm run dev`, then open the URL printed by Vite.
6. Run `npm test` and `npm run build` before submitting changes.

```bash
git clone https://github.com/LAYMmMz/TeamRocket.git
cd TeamRocket/frontend
npm ci
npm run dev
```

If this frontend is on a feature branch, check out `frontend/flight-health` before entering `frontend`, or use the pull request branch selector. No database credentials are needed for mock mode.

## Included

- Seven required dashboards: Mission Medical Command, Individual Astronaut Health, Clinical Examinations & Recovery, Radiation & Environment, Laboratory & Immune Health, Crew Self-Assessment, Ground Medical Review.
- Four fictional crew profiles, each with an interactive, color-personalized 3D suit model. These are illustrative models, not scans or anatomical diagnosis tools.
- Synthetic measurements, 30-point trends, baselines, side/eye/region-specific records, evidence drilldown, symptom forms, private demo check-ins, review notes, procedure acknowledgment, and scenario-driven visual/audio alarms.
- Twelve scenario controls, clearly labeled demo offline/reconnect behavior, browser-local persistence, and role-aware demo navigation.
- The canonical 57-table / 47-feature inventory, research constraints, and proposed FastAPI integration adapter.

## Important integration status

The frontend runs without your unfinished backend. Its compatibility is **contract alignment**, not proof of integration with an implemented API or database. `docs/API_CONTRACT.md` specifies the proposed routes and mapping. Only four API operations are wired: dashboard read, symptom submission, alert acknowledgment, and clinical review. Other modules currently display fixtures or explicit pending-source states. Full database migrations, RLS, authentication UI, Python rules engine, SQLite offline storage, imports, deterministic full-volume seed generation, and cloud sync remain backend/integration work.

The existing `DatabaseSchema.md` is preserved. It conflicts with the final PDF in several table names and suggests direct Supabase/Next.js access. See `docs/SCHEMA_RECONCILIATION.md`; this frontend follows the final PDF's FastAPI boundary.

## Deploy on Vercel

1. Merge the frontend PR when reviewed, or deploy its branch as a preview.
2. In Vercel, choose **Add New → Project**, import `LAYMmMz/TeamRocket`.
3. Set **Root Directory** to `frontend`, **Framework Preset** to `Vite`, build command `npm run build`, output directory `dist`, install command `npm ci`.
4. Set `VITE_DATA_MODE=mock` for the demonstration. Do not add service-role keys or database passwords.
5. Deploy. Open the generated HTTPS URL and test S03, acknowledgment, all seven views (switch demo role to administrator), and profile rotation.
6. Later set `VITE_DATA_MODE=api` and `VITE_API_BASE_URL=https://YOUR-FASTAPI-HOST/api/v1`, then redeploy. Vite environment values are compiled into the frontend; changing them requires a build.
7. Configure FastAPI CORS for the exact production Vercel origin and explicitly approved preview origins. Host persistent onboard SQLite on the onboard/local FastAPI service, not inside the Vercel static frontend.

Vercel config is included in `frontend/vercel.json`. Vercel access and deployment must be completed in your account if no connected deployment tool is available.

Official references checked 15 November 2026: https://vercel.com/docs/frameworks/frontend/vite and https://vite.dev/guide/static-deploy and https://vite.dev/guide/env-and-mode

## Demo walkthrough

- Open Mission command: select any astronaut to view their model and personal observations.
- Enable audio with the top speaker button (browsers require a user gesture).
- Select S03 and Run scenario: a critical demo alert appears while SpO2 stays unavailable.
- Open the alert; inspect the version, evidence, incident ID; acknowledge it. Acknowledgment does not resolve the incident or indicate recovery.
- Use S04 for a single correlated cabin/symptom incident, S07 for stale dosimetry, and S11 to block expired guidance.
- Switch demo role to administrator to inspect all dashboards and the table/feature inventory; choose crew to demonstrate own-record scoping.
- Disconnect demo, submit a report, reload, then reconnect demo. This simulates queued receipts only. It is not a claim of SQLite or cloud synchronization.
- Reset demo returns to the baseline. All local demo changes are fictional and disposable.

## Documentation

- [Implementation guide](docs/IMPLEMENTATION.md)
- [API contract](docs/API_CONTRACT.md)
- [Schema reconciliation](docs/SCHEMA_RECONCILIATION.md)
- [PDF traceability](docs/TRACEABILITY.md)
- [QA and remaining gates](docs/QA.md)

## Project layout

`frontend/src/App.tsx`: views and workflows; `Astronaut.tsx`: generated 3D suit geometry; `types.ts`: contracts, validation, comparison/access helpers; `seed.ts`: fictional display fixtures; `service.ts`: mock and FastAPI boundary; `catalog.json`: all PDF table starter fields and feature IDs; `safety.test.ts`: focused safety tests; `styles.css`: responsive interface.

All mock data are explicitly synthetic. Never enter real medical or confidential information into this public demonstration or its browser-local storage. Demo role switching is not an authentication mechanism. Production access must be enforced by FastAPI and Supabase RLS.
