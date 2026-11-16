# 🚀 RocketPulse — Astronaut Health Monitoring
### TeamRocket | NASA Space Apps Challenge

**One place to understand astronaut health, recognize concerning changes, and support timely medical review.**

[**🌐 Try the live demo (no login required)**](https://teamrocket-rocketpulse.vercel.app) · [**👩‍🚀 Open the crew dashboard**](https://teamrocket-rocketpulse.vercel.app/command) · [**🔎 Check our feature coverage**](frontend/docs/FEATURE_MATRIX.md)

> **For judges:** RocketPulse is a **research prototype using fictional astronauts and synthetic measurements**. Its public demo connects a real React interface, Python FastAPI backend, and Supabase database. It is **not** a medical device, a NASA flight system, or a validated tool for diagnosing health conditions.

---

## 🌍 The challenge

Spaceflight changes the human body. Astronauts may experience **bone and muscle loss, cardiovascular changes, blood-clot concerns, visual changes, altered sleep, radiation exposure, and stress**. Medical information can also arrive from different sensors, examination reports, and manual crew check-ins—sometimes with limited connectivity.

**The problem we're addressing:** How can a crew and its supporting medical team see relevant health information in one place, recognize what needs review, and avoid mistaking missing or unverified data for a healthy reading?

## 💡 Our solution

**RocketPulse** brings together astronaut health observations, trends, symptoms, medical examinations, and mission environmental context in a single monitoring experience.

Our design follows three principles:

1. **See the whole picture.** Organize crew vitals and specialized evidence such as vascular scans, bone-density examinations and laboratory results.
2. **Make uncertainty visible.** Label synthetic and unverified data, preserve its source, and show missing measurements as **unavailable**, not normal.
3. **Keep people in charge.** Support incident and clinical-review workflows instead of automatically diagnosing conditions or recommending treatment.

The project combines a **seven-dashboard frontend**, a **Python backend**, **Supabase PostgreSQL** for cloud data, and **SQLite** for offline-first prototype workflows. The wider specification maps **47 features across 12 monitoring domains**; **not all features are fully implemented, live, or clinically validated**.

## ▶️ Try RocketPulse in about 2 minutes

**[Open the live RocketPulse demo](https://teamrocket-rocketpulse.vercel.app/command)** — no account is needed.

| Step | What to do | What it demonstrates |
| --- | --- | --- |
| **1. Choose an astronaut** | Select **CREW-01**, **CREW-02**, **CREW-03** or **CREW-04**. | A crew-specific view of a fictional mission. |
| **2. Explore vital signs** | Look at **heart rate, blood pressure, oxygen saturation (SpO₂), respiratory measurements**, and their history. | Approved synthetic measurements retrieved from Supabase through FastAPI. |
| **3. Explore the visual interface** | View the **3D astronaut explorer** and switch between dashboard areas. | How different health domains can be organized for fast review. |
| **4. Check the habitat** | Go to **Health Systems → Cabin** and inspect the sample **CO₂** reading. | Crew health can be viewed alongside mission-environment context. |
| **5. Inspect the system connection (optional)** | Open the [public JSON API](https://teamrocket-rocketpulse.vercel.app/api/v1/public/missions/DEMO-01/command?astronaut_id=CREW-01). | The response identifies its source as `supabase-approved-synthetic`. |

**What judges should notice:** The interface uses **database-backed synthetic records** for supported public panels, rather than inventing readings when records are missing. Some other screens describe planned or locally prototyped workflows; those are not represented as live clinical results.

**Direct links:** [Live app](https://teamrocket-rocketpulse.vercel.app) · [Crew API](https://teamrocket-rocketpulse.vercel.app/api/v1/public/missions/DEMO-01/command?astronaut_id=CREW-01) · [Backend health](https://teamrocket-rocketpulse.vercel.app/api/health)

## 🩺 What health risks does RocketPulse cover?

The table below describes the **project's monitoring scope**, not a claim that every examination is available in the public demo.

| Health area | Why it matters | What RocketPulse organizes |
| --- | --- | --- |
| 🩸 **Blood clots (thrombosis)** | Changes in circulation can require careful medical evaluation. | **D-dimer blood-test reports**, left/right **vascular ultrasound** findings, symptoms, and clinician review. **No automatic clot diagnosis.** |
| 🦴 **Bone-density loss** | Extended time in microgravity can affect bones. | **DXA/DEXA scan records**, bone mineral density by body region, and preflight/postflight comparisons. **No invented in-flight scans.** |
| ❤️ **Heart and circulation** | The cardiovascular system adapts to altered gravity and physical activity. | Heart rate, blood pressure, ECG records and individual baselines. |
| 🫁 **Breathing and oxygen** | Respiratory changes and concerning symptoms need attention. | Oxygen saturation, breathing rate and symptom reports—even when a sensor reading is missing. |
| 👁️ **Vision changes / SANS** | Spaceflight can affect the eyes and visual system. | OCT eye imaging, visual acuity, eye-specific findings and follow-up records. |
| 💪 **Muscle and fitness** | Muscle strength and exercise capacity can change during missions. | Exercise sessions, workload, physical assessments and recovery context. |
| ☢️ **Radiation exposure** | Crews and habitats can be exposed to ionizing radiation. | Personal/area dose records, solar-event context and review of measurement quality. |
| 🌡️ **Cabin environment** | Air quality and habitat conditions influence crew wellbeing. | CO₂, cabin pressure, temperature, humidity, light and noise measurements. |
| 🧪 **Immune health and infection** | Testing and sample history support investigation of biological risks. | Blood/other samples, lab assays, microbial tests, and sequencing metadata. |
| 😴 **Sleep, nutrition and wellbeing** | Sleep, hydration, nutrition and behavioral health affect readiness. | Sleep logs, nutrition and fluid balance, and privacy-restricted check-ins. |
| 🧭 **Gravity adaptation and cognition** | Transitioning between gravity conditions affects adaptation and functioning. | Gravity transition notes, vestibular/functional assessments and symptom histories. |
| 🚑 **Medical response and continuity** | Important findings need documentation, follow-up and review. | Alerts, incidents, exam schedules, approved procedure references, inventory and audit records. |

**Examples of safety-aware design:**
- A **D-dimer result** is evidence for medical review—not proof of a blood clot.
- **Bone-density comparisons** require the same anatomical region and appropriate scan method; the system does not fabricate in-flight DXA scans.
- **Missing SpO₂** does not suppress a serious breathing-symptom report.
- **Radiation totals** are only compared when quantities, units and time intervals are compatible.
- **Sensitive behavioral data** is restricted, not shared on the public dashboard.

For a full feature-by-feature checklist, see [the 47-feature matrix](frontend/docs/FEATURE_MATRIX.md).

## ✅ What's working, and what's still a prototype?

| Capability | Status for this submission |
| --- | --- |
| Public React dashboard and 3D astronaut explorer | **Available to judges** without login |
| Python FastAPI ↔ Supabase ↔ frontend data path | **Integrated for approved public synthetic reads** |
| Crew-specific vitals, historical trends and cabin example | **Demonstrated using synthetic cloud records** |
| Blood-clot, bone, OCT, lab and other specialized domain structures | **Schema designs and/or protected local synthetic staging contracts**; not all public or cloud-backed |
| Authenticated alerts, incidents, examination and offline/sync components | **Backend prototype workflows** with role and mission boundaries; not all end-to-end cloud paths verified |
| Full 47-feature acceptance, operational sensors and clinical diagnosis | **Not claimed** |

For the November 16, 2026 integration build, repository documentation reports **428 approved synthetic public measurement rows**, a **24-point** historical trend response, and a cabin example including **650 ppm CO₂**. These are **fixed demonstration readings, not live astronaut telemetry**. A backend health response proves service availability, not completion of protected clinical synchronization.

Read the [implementation and acceptance audit](docs/PDF_ALIGNMENT_STATUS.md) for verified behavior and remaining work.

## 🧩 How the technology works

```text
               JUDGES' WEB BROWSER
          React + TypeScript dashboard
                       |
                public GET requests
                       v
             Python FastAPI backend
                       |
           approved read-only access
                       v
           Supabase PostgreSQL cloud
              synthetic demo data

Separate authenticated prototype workflows:
  FastAPI → encrypted offline SQLite → sync queue
         → authorized Supabase RPC (when configured)
```

- **Frontend:** React, TypeScript and Vite, deployed to **Vercel**.
- **Backend:** Python and FastAPI, deployed to **Railway**.
- **Cloud database:** **Supabase PostgreSQL**, with row-level security and an isolated read-only public feed.
- **Offline storage:** Encrypted **SQLite**, with queueing and receipt-based synchronization in authorized workflows.

The broader database design includes crew profiles, mission assignments, health observations, vascular ultrasound, bone scans, eye exams, laboratory results, environmental readings, alerts, incidents, inventory and audit records. **The 57-table cloud inventory is a design target, not proof that all 57 tables exist in the deployed project.**

For reviewers interested in implementation details: [database inventory](frontend/docs/DATABASE_MAP.md) · [database architecture](database/docs/DatabaseSchema.md) · [backend modules and local setup](backend/README.md) · [frontend](frontend/) · [API integration](backend/app/integrations/) · [domain validation logic](backend/app/domain2/clinical_logic.py).

## 🔐 Privacy, limitations and scientific responsibility

RocketPulse uses **fictional crew members and synthetic data only** in its public demo. Public endpoints are **read-only**; protected clinical records, behavioral check-ins, clinical writes and mission-authorized synchronization are not open to visitors.

The prototype **does not diagnose blood clots, osteoporosis, SANS, infection or other conditions**, prescribe medication, authorize mission activities, or replace qualified medical personnel. Clinical findings require appropriate source evidence, method and unit checks, and human review.

## 🛠️ Technical setup and deployment

**Judges can stop reading here and use the [live demo](https://teamrocket-rocketpulse.vercel.app).** The sections below are for developers and technical reviewers who want to reproduce or inspect the integration.

### Deploy the integrated application

> **How to host all three parts:** Vercel runs the **frontend**, Railway runs the **FastAPI backend** and persistent SQLite, and Supabase hosts the **cloud PostgreSQL database**. Vercel itself does not execute the FastAPI container or host PostgreSQL. The `frontend/vercel.json` rewrite connects them under **one public web address**.

#### 1. GitHub repository

Use [**LAYMmMz/TeamRocket**](https://github.com/LAYMmMz/TeamRocket). The currently published integration source is `feat/frontend-backend-api-integration` (the repository's current default branch). Do not deploy files from `archive/` or assume a historical `main` branch contains this integration. Keep backend and frontend changes together in the same review workflow and check GitHub Actions before publishing.

#### 2. Supabase database (existing TeamRocket project)

- Project: **TeamRocketV2Database**, ID `ziecxjoeljxoocixejtz`.
- Endpoint: `https://ziecxjoeljxoocixejtz.supabase.co`.
- **This existing project already has the reviewed public feed installed.** For a different/new project, the project owner must review and execute [`supabase/manual/20261116_public_demo_feed.sql`](supabase/manual/20261116_public_demo_feed.sql) in that project's SQL Editor. This script creates/seeds **only** the isolated public demonstration table; it does **not** recreate all protected clinical tables or authentication configuration.
- Confirm its final audit: `visible_to_anonymous=428` or more; anonymous `SELECT` permitted, anonymous `INSERT`, `UPDATE`, `DELETE` denied; RLS enabled. Never change the privileged `health_logs` or `ingest_sync_event` policies to make public demos work.
- **Never put a Supabase `service_role`/secret key or database password in Vercel's `VITE_*` environment variables, public code, screenshots or commit history.**

#### 3. Railway backend (Docker + persistent data)

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

#### 4. Vercel frontend (public judge link)

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

#### 5. Verify the complete judge deployment (no login)

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

### Local development and tests

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

### Additional data-protection notes

- The **public** dataset contains **428 clearly labelled synthetic rows** approved for read-only display. Historical observations are loaded from Supabase PostgreSQL via Railway; display-only fictional crew names are generated by the public API. No private crew profiles are exposed.
- **Protected** clinical endpoints, user JWTs, offline sync queue, audit trails, attachments and patient/crew-specific records are **not available** to anonymous judges. The public UI intentionally does not create measurements or acknowledge private alerts.
- FastAPI also runs an **encrypted local SQLite** store on a Railway volume; the authorized synchronization pathway is separate from public dashboard reads. **Unattended 24/7 private cloud sync is not enabled or verified**; do not claim it is.
- The app contains seven dashboard views and additional engineering/simulation screens, but some features are research references or UI demonstrations rather than independently accepted medical functions. A passing public JSON read does **not** prove every module, alert, or historical acceptance test has passed.
- Use this as a **research and educational hackathon prototype**, never as a clinical decision system.

---

**Team:** [TeamRocket](https://github.com/LAYMmMz/TeamRocket) · **Deployment:** [Vercel](https://vercel.com/laymmmzs-projects/teamrocket-rocketpulse) + [Railway](https://railway.com/) + [Supabase](https://supabase.com/dashboard/project/ziecxjoeljxoocixejtz) · **Data:** approved synthetic only.
