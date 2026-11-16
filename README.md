# RocketPulse | TeamRocket 🚀

**NASA Space Apps Challenge — Astronaut Health-Monitoring Research Prototype**

[**🌐 Open the Judges' Live Demo (no login)**](https://teamrocket-rocketpulse.vercel.app) · [**📊 Live Synthetic API Sample**](https://teamrocket-rocketpulse.vercel.app/api/v1/public/missions/DEMO-01/command?astronaut_id=CREW-01) · [**🩺 API Health**](https://teamrocket-rocketpulse.vercel.app/api/health) · [**⚙️ Deployment Guide**](#deploy-the-integrated-application) · [**🔐 Data Safety**](#data-protection-and-honest-scope)

> **Judge notice:** The app is a *working three-service integration* for a **fictional, synthetic mission**: React on Vercel reads an approved dataset from Supabase through a FastAPI service on Railway. It is **not** NASA operational telemetry, a medical device, or a completed validation of all proposed clinical features. Public visitors do not need a login and cannot edit the database.

## PDF scope and implementation status

The specification covers **47 features, seven dashboards, 12 monitoring domains, five hazards, 57 logical cloud tables, six SQLite tables and 12 scenarios**. See the [complete feature matrix](frontend/docs/FEATURE_MATRIX.md), [database-read changes and remaining acceptance blockers](docs/PDF_ALIGNMENT_STATUS.md), and the application's **Feature Status** menu (`/coverage`).

Database mode now requests selected-crew records for dashboard panels, the body explorer and feature pages. Missing records stay unavailable. Undefined medical indices are excluded; they cannot substitute for method-specific laboratory or examination evidence. Public visitors can read approved synthetic data but cannot execute protected clinical writes or sync. The 47 feature entries are not a claim that all 47 clinical workflows have passed acceptance.

## Start here: judge walkthrough

1. **[Open RocketPulse](https://teamrocket-rocketpulse.vercel.app/command)** — the command dashboard and 3D crew explorer are public.
2. Select a fictional crew member (**CREW-01** through **CREW-04**). View the **heart rate, SpO₂, respiration and blood-pressure** samples pulled from Supabase, plus the historical trend graph.
3. Explore the other dashboards, **Health Systems → Cabin** (the synthetic CO₂ reading) and the architecture shown in **Integration**. Reference/scenario content is labelled as demonstrative; some proposed modules are not cloud-backed.
4. **[Open the JSON API in another tab](https://teamrocket-rocketpulse.vercel.app/api/v1/public/missions/DEMO-01/command?astronaut_id=CREW-01)** and verify the source marker `"data_source": "supabase-approved-synthetic"`, `"is_synthetic": true`, and fictional crew names. This API is reached through the same public Vercel origin as the frontend.
5. **[Check the backend health endpoint](https://teamrocket-rocketpulse.vercel.app/api/health)**. `status=ok` shows the API is running; it is **not** proof of private cloud writes.

**Stable submission URL:** https://teamrocket-rocketpulse.vercel.app

## How the three services connect

```text
Judges' browser (no application login)
    |
    v
Vercel — React + TypeScript + Vite + seven dashboard views
    |   VITE_DATA_MODE=public, /api/v1 same-origin rewrites
    v
Railway — FastAPI  /api/v1/public/*   (GET-only allowlist)
    |   Public Supabase publishable key / anonymous RLS
    v
Supabase — TeamRocketV2Database (PostgreSQL)
    |   public.rocketpulse_public_demo_samples
    |   428 fictional measurements, explicitly approved for anonymous reads
    +--> separate protected clinical tables and privileged RPC (NOT public)

Private, authenticated workflows (separate path):
    FastAPI -> encrypted local SQLite /data -> durable outbox
       -> mission-authorized Supabase RPC when a permitted session requests sync
```

**Verified in the integration build (November 16, 2026):** The public command API returned **HTTP 200** with actual Supabase-approved synthetic readings; the trends endpoint returned **24 historical time points**; the Cabin domain endpoint returned **HTTP 200**, including a synthetic **650 ppm CO₂** sample. The 428-row table's anonymous visibility was confirmed through the Supabase SQL Editor. These samples are fixed demonstrative readings, **not live sensors**.

### Repository map

| Path | Purpose |
| --- | --- |
| [`frontend/`](frontend/) | Seven RocketPulse dashboards, 3D crew scene, Vite application, Vercel rewrites |
| [`frontend/src/lib/api.ts`](frontend/src/lib/api.ts) | Read-only public routes vs. private JWT-required routes |
| [`frontend/vercel.json`](frontend/vercel.json) | Proxy `/api/v1/*` and `/api/health` to Railway; SPA fallback |
| [`backend/`](backend/) | FastAPI, offline encrypted SQLite store, auth, queue, tests |
| [`backend/app/integrations/public_demo_api.py`](backend/app/integrations/public_demo_api.py) | Public `GET` API: approved synthetic Supabase rows only |
| [`backend/Dockerfile`](backend/Dockerfile) / [`railway.json`](railway.json) | Docker and persistent backend deployment |
| [`supabase/manual/20261116_public_demo_feed.sql`](supabase/manual/20261116_public_demo_feed.sql) | One-time 428-row synthetic feed, anonymous SELECT policy, RLS |
| [`supabase/migrations/`](supabase/migrations/) | Historical cloud migrations; **not a complete fresh project bootstrap** |
| [`docs/PUBLIC_SUPABASE_DEMO.md`](docs/PUBLIC_SUPABASE_DEMO.md) | Full public-data threat boundaries and database verification |
| [`docs/INTEGRATION_DEPLOYMENT.md`](docs/INTEGRATION_DEPLOYMENT.md) | Authenticated private sync and legacy integration details |
| [`docs/REPOSITORY_ORGANIZATION.md`](docs/REPOSITORY_ORGANIZATION.md) | Consolidated branches and archived components |

## Health monitoring, clinical records and backend capabilities

RocketPulse is more than a vitals chart: its **research specification spans 12 monitoring domains**, and the Python backend contains protected APIs, clinical evidence contracts and local persistence for many of them. The distinctions below matter: **a table in the specification is not automatically a deployed Supabase table; a validated local record is not automatically synchronized; a UI page does not prove a clinical diagnostic capability**. The public judge demo currently exposes only its approved synthetic observation feed.

### Clinical and environmental monitoring inventory

| Area | Measurements, examinations and workflow | Schema / backend references | Current scope |
| --- | --- | --- | --- |
| **Blood clots / vascular thrombosis** (F15) | D-dimer and other method-specific laboratory results; side-specific vascular ultrasound with vein/site, flow and clinician-reviewed thrombus findings. Symptoms can be captured and escalated separately. | `laboratory_results`, `biological_samples`, `vascular_ultrasound_results`, `medical_findings`; `backend/app/domain2/{contracts,clinical_logic}.py` (`vascular`, `lab_results`) | Structured synthetic staging/review contracts; **no automatic blood-clot detection or diagnosis**. Unreviewed D-dimer does not establish thrombosis. |
| **Bone density / bone loss** (F20) | DXA/DEXA scan sessions, site-specific bone mineral density (BMD), T/Z-scores where supplied, preflight-versus-postflight comparisons and examination review. | `bone_scans`, `bone_density_results`, `medical_exam_schedule`; domain `bone` | Prototype contract accepts **PRE/POST** flight phases; **no fabricated in-flight DXA/BMD readings** or automatic osteoporosis diagnosis. |
| **Heart and circulation** (F13) | Heart rate, blood pressure, ECG reports/waveform references, activity context and personal baselines. | `vital_signs`, `ecg_records`, `health_baselines`; `backend/app/vitals/`, `backend/app/domain2/` | Public synthetic vitals/trends; additional authenticated clinical APIs and local synthetic models. |
| **Breathing and oxygenation** (F14) | Respiratory rate, SpO₂, breathing symptoms and trends, including incidents when a sensor reading is missing. | `vital_signs`, `symptom_reports`, `medical_incidents`; `backend/app/measurements/`, `backend/app/incidents/` | Synthetic observations and serious-symptom escalation; missing SpO₂ is never silently treated as normal. |
| **Vision and SANS** (F21) | Optical coherence tomography (OCT), eye-specific assessments, visual acuity and fundoscopy findings, with methods and reviewer context. | `ocular_assessments`, `ocular_results`; domain `ocular` | Eye-/region-/method-matched review records, not automated SANS diagnosis. |
| **Muscle, exercise and fitness** (F18–F19) | Exercise duration, workload, adherence, strength and fitness tests with protocol-aware comparisons. | `exercise_sessions`, `fitness_assessments`, `functional_assessments`; domains `exercise`, `fitness` | Activity and assessment evidence; comparability depends on matching test protocol. |
| **Microgravity and vestibular health** (F16–F17) | Gravity transitions, adaptation symptoms, balance and functional/cognitive assessments. | `gravity_transition_events`, `functional_assessments`, `symptom_reports`; domain `gravity` | Record/review workflows only; no autonomous EVA or fitness-for-duty clearance. |
| **Sleep, nutrition, hydration and wellbeing** (F22–F24) | Sleep sessions, circadian trends, meals/macronutrients, fluid balance and sensitive behavioral check-ins. | `sleep_sessions`, `nutrition_logs`, `fluid_balance_logs`, `behavioral_checkins`; domains `sleep`, `nutrition`, `hydration`, `behavioral` | Synthetic records and trends; behavioral entries are role-restricted. |
| **Radiation and solar events** (F25–F26) | Crew and habitat dosimetry, particle/event context, measurement intervals, detector freshness and incident review. | `personal_dose_records`, `radiation_area_records`, `radiation_events`; domains `radiation`, `dose_events` | Descriptive evidence. Dose quantities/units and intervals must be compatible; never convert Gy to Sv without validated context. |
| **Cabin atmosphere and habitat** (F27–F28) | CO₂, pressure, temperature, humidity, light and noise with zone, calibration and averaging window. | `environmental_readings`, `mission_locations`; domains `environment`, `habitat_events` | Public synthetic cabin example plus private evidence contracts; no unsanctioned operational alarm thresholds. |
| **Immune, infection and laboratory testing** (F29–F35) | Blood/saliva/urine sampling, specimen custody, assays, immune/viral markers, surface/water/air microbiology, sequencing and QC. | `biological_samples`, `clinical_sample_chain`, `laboratory_results`, `environmental_samples`, `environmental_lab_results`, `microbial_identifications`, `sequencing_runs`; domains `samples`, `lab_results`, `environmental_samples`, `sequencing` | Method- and specimen-aware synthetic staging; no invented immune score or pathogen diagnosis. |
| **Medical operations** (F01–F12, F36–F39) | Mission/crew/device management, provenance, baseline rules, symptom reporting, alerts, medical incidents, examinations, procedure guidance, supply inventory, audit and sync. | `missions`, `astronauts`, `mission_crew`, `device_assignments`, `alert_rules`, `health_alerts`, `alert_evidence`, `incident_events`, `medical_procedures`, `medical_inventory`, `sync_receipts`, `audit_logs`; `backend/app/{foundation,alerts,incidents,examinations,procedures,inventory,sync}/` | Authenticated prototype workflows. Approved/versioned rules and human escalation are required; this is not clinical decision support validated for use in space. |

For the exact **47 feature IDs**, seven dashboards and 12 scenario definitions, see [the feature matrix](frontend/docs/FEATURE_MATRIX.md). For the fuller cloud table inventory and six required offline tables, see [the database mapping](frontend/docs/DATABASE_MAP.md). These inventories describe the **intended logical schema**; check the [alignment audit](docs/PDF_ALIGNMENT_STATUS.md) for what has actually been verified.

### Backend implementation and API boundaries

The [FastAPI backend](backend/app/) uses protected, mission-scoped endpoints and **two distinct local SQLite paths**: Dev 1's encrypted offline store/outbox and Dev 2's separate clinical/demo models. Important components include:

- **Identity, ingestion and baselines:** `auth/`, `foundation/`, `measurements/`, `vitals/`, and `domain2/baselines.py` handle permissions, crew/missions, provenance, unit-aware measurements and reference baselines.
- **Clinical safety and review:** `alerts/`, `incidents/`, `examinations/`, `procedures/` and `domain2/clinical_logic.py` cover evidence-linked alert/incident workflows, scheduling and conservative *descriptive* comparisons. Serious reported symptoms can create incidents without requiring an SpO₂ measurement. The code does **not** prescribe treatments, diagnose clots, invent alert thresholds or authorize EVA.
- **Other services:** `radiation/`, `environment/`, `samples/`, `wellness/`, `inventory/`, `reports/`, `simulation/` and `nasa/` contain supporting module APIs and research/synthetic workflows.
- **Staging evidence API:** `GET /api/domain2/catalog`, `POST /api/domain2/{domain}` and `GET /api/domain2/{domain}?mission_id=...` use [typed contracts](backend/app/domain2/contracts.py) for 23 domains, including `vascular`, `bone`, `ocular`, `lab_results` and `symptoms`. Writes require authenticated mission access, development/test environment and **synthetic** source records; domain2 records remain in the encrypted local store with **cloud sync disabled for those record types**. The `behavioral` domain has additional privacy checks.
- **Dashboard/API adapter:** `backend/app/integrations/frontend_api.py` provides protected `/api/v1` dashboard, trends, domain-record, symptom, alert-acknowledgment and sync routes. `public_demo_api.py` separately serves **GET-only** approved Supabase synthetic rows under `/api/v1/public/*`; this is **not a general-purpose anonymous clinical API**.
- **Offline and cloud delivery:** `offline/store.py`, `sync/worker.py`, `cloud_completion/outbox.py` and reviewed Supabase `ingest_sync_event` RPC migrations support queued/retryable delivery with receipts. **Local persistence, a queued event, and a cloud-acknowledged clinical record are different states**. Live private synchronization requires valid mission-authorized credentials, checked receipts and the corresponding cloud schema.

Explore the running development server at `http://127.0.0.1:8000/docs`; route availability and authorization depend on mode and configuration. See [backend setup and tests](backend/README.md) and [integration documentation](docs/INTEGRATION_DEPLOYMENT.md).

### Database structure, privacy and validation status

**Supabase PostgreSQL (cloud):** The design includes mission membership/RBAC, crew/device identity, vitals/ECG, physiological baselines, clinical examinations (vascular, bone, eye), laboratory samples/results, radiation/environment, alerts/incidents, procedures, inventory, quality/provenance, attachments and sync receipts. [Database schema documentation](database/docs/DatabaseSchema.md) describes many tables and their intended constraints; [the 57-table data dictionary](frontend/docs/DATABASE_MAP.md) provides the broader specification. **These are schema designs, not proof that 57 physical tables exist or are fully migrated in the deployed Supabase project.** Migrations in `supabase/migrations/` are incremental, not a clean complete bootstrap.

**Local SQLite (offline):** The six-table minimum design contains `offline_vital_signs`, `offline_symptom_reports`, `offline_health_alerts`, `offline_alert_rules`, `offline_medical_procedures` and `sync_queue`. Separate Dev 2 SQLAlchemy models support extra synthetic clinical evidence. Do not mistake the reference six-table mapping for a verified physical deployment of every required table.

**Provenance:** Medical observations should carry mission/crew identity, `event_id`, source/device and method, `measured_at` versus `received_at`, raw and normalized unit/value where appropriate, quality/verification/review state, and `is_synthetic`. Missing or unverified data stays unavailable, never assumed healthy. Anatomical region, laterality, eye, method and specimen details are necessary before drawing comparisons. Private tables and behavioral records require authentication, authorization and appropriate RLS.

**Public demonstration:** Only the separately approved `rocketpulse_public_demo_samples` feed is anonymous-readable (428 synthetic samples documented for this integration build); it does **not** include sufficient verified D-dimer, vascular-ultrasound, DXA, OCT or laboratory examination data to claim that those specialized modules are live or clinically validated. The public UI filters unsupported made-up medical indices. See [the public-data boundary](docs/PUBLIC_SUPABASE_DEMO.md) and [remaining acceptance blockers](docs/PDF_ALIGNMENT_STATUS.md).

## Deploy the integrated application

> **How to host all three parts:** Vercel runs the **frontend**, Railway runs the **FastAPI backend** and persistent SQLite, and Supabase hosts the **cloud PostgreSQL database**. Vercel itself does not execute the FastAPI container or host PostgreSQL. The `frontend/vercel.json` rewrite connects them under **one public web address**.

### 1. GitHub repository

Use [**LAYMmMz/TeamRocket**](https://github.com/LAYMmMz/TeamRocket). The currently published integration source is `feat/frontend-backend-api-integration` (the repository's current default branch). Do not deploy files from `archive/` or assume a historical `main` branch contains this integration. Keep backend and frontend changes together in the same review workflow and check GitHub Actions before publishing.

### 2. Supabase database (existing TeamRocket project)

- Project: **TeamRocketV2Database**, ID `ziecxjoeljxoocixejtz`.
- Endpoint: `https://ziecxjoeljxoocixejtz.supabase.co`.
- **This existing project already has the reviewed public feed installed.** For a different/new project, the project owner must review and execute [`supabase/manual/20261116_public_demo_feed.sql`](supabase/manual/20261116_public_demo_feed.sql) in that project's SQL Editor. This script creates/seeds **only** the isolated public demonstration table; it does **not** recreate all protected clinical tables or authentication configuration.
- Confirm its final audit: `visible_to_anonymous=428` or more; anonymous `SELECT` permitted, anonymous `INSERT`, `UPDATE`, `DELETE` denied; RLS enabled. Never change the privileged `health_logs` or `ingest_sync_event` policies to make public demos work.
- **Never put a Supabase `service_role`/secret key or database password in Vercel's `VITE_*` environment variables, public code, screenshots or commit history.**

### 3. Railway backend (Docker + persistent data)

Existing instance: [**TeamRocket-Astronaut-Health**](https://railway.com/) → staging → `teamrocket-fastapi`.

Create/link a Railway service from this GitHub repository, deploying the integration branch. Configure:

| Railway setting | Value |
| --- | --- |
| Builder | **Dockerfile**, path `backend/Dockerfile` |
| Docker build context | Repository root (Dockerfile copies `backend/` and `docs/schema-handoff.json`) |
| Health check | `/api/health` |
| Public service URL (current) | `https://teamrocket-fastapi-staging.up.railway.app` |
| Durable volume | Mount `/data` for encrypted SQLite and attachments |
| `APP_ENV` | `test` for the *existing synthetic judge staging service*; do not label it a clinical production backend |
| `SQLITE_PATH` | `/data/offline.db` |
| `DEV2_DATABASE_URL` | `sqlite:////data/dev2_clinical.db` |
| `ATTACHMENTS_ROOT` | `/data/attachments` |
| `SCHEMA_MANIFEST_PATH` | `/srv/docs/schema-handoff.json` |
| `SUPABASE_URL` | `https://ziecxjoeljxoocixejtz.supabase.co` |
| `SUPABASE_ANON_KEY` | The project's **public publishable key** (Railway server variable, not a service-role secret) |
| `SYNC_RPC_URL` | `https://ziecxjoeljxoocixejtz.supabase.co/rest/v1/rpc/ingest_sync_event` (private, mission-authorized sync only) |
| `SYNC_ACCESS_TOKEN` | **Leave empty** — do not save a user's expiring JWT as a permanent worker secret |

Also set `LOCAL_ENCRYPTION_KEY` (persistent **Fernet** key), `OFFLINE_GRANT_SECRET` (random 32+ characters), and the project's `AUTH_ISSUER`, `AUTH_JWKS_URL`, `AUTH_AUDIENCE=authenticated` for protected APIs. See [the backend setup guide](backend/README.md) for local development. **Do not rotate the Fernet key without an encrypted-data migration.** Keep the Railway service and its volume operational during judging.

### 4. Vercel frontend (public judge link)

Existing project: [**teamrocket-rocketpulse on Vercel**](https://vercel.com/laymmmzs-projects/teamrocket-rocketpulse).

In Vercel, import/connect **`LAYMmMz/TeamRocket`**, use the **current integration/default branch** as Production Branch, and set:

| Vercel setting | Value |
| --- | --- |
| Framework Preset | **Vite** |
| Root Directory | **`frontend`** |
| Node.js Version | **24.x** |
| Install Command | **`npm ci`** |
| Build Command | **`npm run build`** |
| Output Directory | **`dist`** |
| Production `VITE_DATA_MODE` | **`public`** — not `demo` or `api` |
| Production `VITE_API_BASE_URL` | **`/api/v1`** (same-origin proxy) |

`VITE_DATA_MODE=public` bypasses the application's login screen and only calls the **GET-only**, synthetic Supabase-backed `/api/v1/public/*` API. `VITE_DATA_MODE=demo` uses local static browser fixtures (not database-backed); `VITE_DATA_MODE=api` is the **private** JWT-protected mode requiring user login.

Ensure the production domain is **publicly accessible to judges**; if Vercel Deployment Protection redirects visitors to Vercel login, limit protection to previews in **Project Settings → Deployment Protection**. Click **Redeploy** after changing build-time environment variables: Vite embeds them during the build. If the Railway backend URL changes, update [`frontend/vercel.json`](frontend/vercel.json) and redeploy Vercel.

After deployment, submit the **stable production URL**: **https://teamrocket-rocketpulse.vercel.app**, not a temporary preview/build URL.

### 5. Verify the complete judge deployment (no login)

Open these URLs in a private/incognito browser and verify **JSON**, not `index.html`:

| Test | Expected |
| --- | --- |
| [App homepage](https://teamrocket-rocketpulse.vercel.app) | RocketPulse dashboard, **no app or Vercel login** |
| [FastAPI health through Vercel](https://teamrocket-rocketpulse.vercel.app/api/health) | JSON: `status=ok` |
| [Crew command API](https://teamrocket-rocketpulse.vercel.app/api/v1/public/missions/DEMO-01/command?astronaut_id=CREW-01) | HTTP 200; `data_source=supabase-approved-synthetic` |
| [Crew trends API](https://teamrocket-rocketpulse.vercel.app/api/v1/public/measurements/trends?astronaut_id=CREW-01) | 24 historical synthetic chart points |
| [Cabin domain API](https://teamrocket-rocketpulse.vercel.app/api/v1/public/reports/domains/cabin?astronaut_id=CREW-01) | HTTP 200 and synthetic CO₂ sample |
| Private `/api/v1/missions/DEMO-01/command?astronaut_id=CREW-01` | **401 without Supabase user JWT**; expected |
| Public `POST /api/v1/public/...` | **405**; public modifications forbidden |

**Troubleshooting:** If a public API URL shows the RocketPulse HTML shell, Vercel deployed the wrong source/branch or lost the `frontend/vercel.json` rewrites. If it returns **503**, check the Supabase feed table, read-only RLS policy, and Railway `SUPABASE_URL`/`SUPABASE_ANON_KEY` rather than exposing private tables. If a browser asks for a login, check `VITE_DATA_MODE=public` and Vercel Deployment Protection.

## Local development and tests

```powershell
git clone https://github.com/LAYMmMz/TeamRocket.git
cd TeamRocket
cd frontend
npm ci
npm run check:scope
npm run build
npm run dev
```

For the **database-connected public** frontend locally, create an untracked `frontend/.env.local` containing `VITE_DATA_MODE=public` and `VITE_API_BASE_URL=/api/v1`. The local Vite server proxies `/api` to FastAPI at `127.0.0.1:8000`; run the configured backend alongside Vite. The hosted Vercel proxy is defined by `frontend/vercel.json`. For backend local tests, see [`backend/README.md`](backend/README.md). GitHub Actions runs the frontend build and integration API tests.

## Data protection and honest scope

- The **public** dataset contains **428 clearly labelled synthetic rows** approved for read-only display. Historical observations are loaded from Supabase PostgreSQL via Railway; display-only fictional crew names are generated by the public API. No private crew profiles are exposed.
- **Protected** clinical endpoints, user JWTs, offline sync queue, audit trails, attachments and patient/crew-specific records are **not available** to anonymous judges. The public UI intentionally does not create measurements or acknowledge private alerts.
- FastAPI also runs an **encrypted local SQLite** store on a Railway volume; the authorized synchronization pathway is separate from public dashboard reads. **Unattended 24/7 private cloud sync is not enabled or verified**; do not claim it is.
- The app contains seven dashboard views and additional engineering/simulation screens, but some features are research references or UI demonstrations rather than independently accepted medical functions. A passing public JSON read does **not** prove every module, alert, or historical acceptance test has passed.
- Use this as a **research and educational hackathon prototype**, never as a clinical decision system.

---

**Team:** [TeamRocket](https://github.com/LAYMmMz/TeamRocket) · **Deployment:** [Vercel](https://vercel.com/laymmmzs-projects/teamrocket-rocketpulse) + [Railway](https://railway.com/) + [Supabase](https://supabase.com/dashboard/project/ziecxjoeljxoocixejtz) · **Data:** approved synthetic only.
