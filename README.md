# 🚀 RocketPulse — Astronaut Health Monitoring

**TeamRocket · NASA Space Apps Challenge · Synthetic-data research prototype**

**RocketPulse helps a mission team see fragmented astronaut-health observations in one place, trace their sources, and recognize what needs human medical review—without treating missing data as normal.**

[**🌐 Launch the live demo**](https://teamrocket-rocketpulse.vercel.app/command) · [**🧭 Follow the judge walkthrough**](#-3-minute-judge-walkthrough) · [**🗃️ Inspect Supabase verification**](https://teamrocket-rocketpulse.vercel.app/data-model) · [**📋 Explore the 47-feature matrix**](frontend/docs/FEATURE_MATRIX.md)

> **Important for judges:** This is an independently built **educational/research prototype**, not a NASA-operated system or medical device. All public crew identifiers and observations are **fictional and synthetic**. Our public site demonstrates a genuine **React → FastAPI → Supabase** read path; it does **not** claim that all 47 clinical workflows, 12 end-to-end acceptance scenarios, or offline-to-cloud synchronization are complete.

## 🎯 The problem and our approach

During a mission, cardiovascular readings, environmental observations, symptoms, exercise history, examination reports and laboratory results may come from different sources. When communication is delayed, a medical reviewer must understand **who** a record concerns, **when** it was measured, **where** it came from, and **whether** it is verified.

RocketPulse organizes this evidence into a mission-control interface designed around three principles: **(1)** source-aware monitoring across crew and habitat, **(2)** honest missing/stale/simulated-data states, and **(3)** human authorization and review for clinical decisions. Our design follows the team's *NASA Astronaut Health Monitoring System — Final Development MasterDocs*, edition **15 November 2026**.

## ▶️ 3-minute judge walkthrough

**Start here: [teamrocket-rocketpulse.vercel.app/command](https://teamrocket-rocketpulse.vercel.app/command). No login is required for the public synthetic demo.**

| Step | Try this | What you can verify |
| --- | --- | --- |
| **1 · Mission overview** | Open [Mission Medical Command](https://teamrocket-rocketpulse.vercel.app/command) and choose **CREW-01**; switch to another fictional crew member. | Crew-specific synthetic mission observations, timestamps and status labels. |
| **2 · Health readings** | Visit [Individual Astronaut Health](https://teamrocket-rocketpulse.vercel.app/individual) and the [Health Systems catalog](https://teamrocket-rocketpulse.vercel.app/domains). | Trends and domain records retrieved through the public FastAPI/Supabase feed where approved samples exist. |
| **3 · Interactive explorer** | Open the [3D Crew Health Explorer](https://teamrocket-rocketpulse.vercel.app/explorer) and select body regions. | A navigable body-to-health-domain interface—not a medical scan. |
| **4 · Mission context** | Open the [Cabin Environment domain](https://teamrocket-rocketpulse.vercel.app/domains/cabin). | Synthetic habitat readings, including CO₂ examples with source information. |
| **5 · Evidence and scenarios** | Open [Mission Scenarios](https://teamrocket-rocketpulse.vercel.app/simulation), then choose S04 or S07. | Related database samples alongside scenario requirements, **not** falsely labeled executed or passed tests. |
| **6 · Real database proof** | Open [Data Tables](https://teamrocket-rocketpulse.vercel.app/data-model). | An operator-verified **57-table Supabase starter-field snapshot**, inspection timestamp and approved synthetic seed counts. |

For a machine-readable connection check, open the [public crew JSON API](https://teamrocket-rocketpulse.vercel.app/api/v1/public/missions/DEMO-01/command?astronaut_id=CREW-01) or [approved schema JSON API](https://teamrocket-rocketpulse.vercel.app/api/v1/public/schema/catalog). The public API has **no private clinical write access**.

## 🛰️ What is in the project?

The MasterDocs defines **five spaceflight hazards**, **12 monitoring domains**, **seven role-oriented dashboards**, **47 feature deliverables**, **57 cloud tables**, **six onboard SQLite tables** and **12 required scenarios**. These numbers describe the **required scope**; they are not a claim of complete acceptance.

**Five hazards:** Space Radiation · Isolation & Confinement · Distance from Earth · Gravity Fields · Hostile / Closed Environments.

**Twelve health/mission domains:** Cardiovascular & Respiratory; Vascular/Thrombosis; Radiation; Gravity/Vestibular; Fitness/Muscle; Bone; Vision/SANS; Immune/Infection; Sleep/Behavior; Cabin Environment; Environmental Microbiology; Autonomous Medical Operations.

### Seven dashboard views

All seven PDF-defined dashboard **routes** exist and can be opened. A navigable screen is not automatically a completed medical workflow.

| MasterDocs dashboard | Public route | Intended focus |
| --- | --- | --- |
| Mission Medical Command (F40) | [Open](https://teamrocket-rocketpulse.vercel.app/command) | Crew overview, mission state and evidence navigation |
| Individual Astronaut Health (F41) | [Open](https://teamrocket-rocketpulse.vercel.app/individual) | Vitals, observations, trends and history |
| Clinical Examinations & Recovery (F42) | [Open](https://teamrocket-rocketpulse.vercel.app/examinations) | Vascular, eye, bone, fitness and examination review |
| Radiation & Environment (F43) | [Open](https://teamrocket-rocketpulse.vercel.app/environment) | Dose, habitat and environmental context |
| Laboratory & Immune Health (F44) | [Open](https://teamrocket-rocketpulse.vercel.app/laboratory) | Samples, assay results and research evidence |
| Crew Self-Assessment (F45) | [Open](https://teamrocket-rocketpulse.vercel.app/crew) | Symptoms, fatigue and restricted self-reports |
| Ground Medical Review (F46) | [Open](https://teamrocket-rocketpulse.vercel.app/ground) | Clinical review, incidents and synchronization concepts |

**Protected clinical addition (PR #13):** Authorized `admin` / `flight_surgeon` roles can request **synthetic local SQLite** examination and laboratory evidence in development/test API mode. These readers preserve ultrasound laterality, OCT eye/region, pre-/postflight DXA context, assay methods, and sample custody. They are **not public Supabase clinical-record endpoints**, and the judge-facing no-login site does not reveal their records.

## ✅ What is verified vs. still being developed?

| Capability | Evidence available now | Boundary / remaining work |
| --- | --- | --- |
| **Public web application** | Deployed React/TypeScript/Vite frontend on Vercel; accessible without a user account | A working page is not clinical certification |
| **Database-backed public observations** | FastAPI on Railway reads approved synthetic Supabase samples for crew/health domains | No real astronaut or sensor telemetry |
| **Cloud inventory** | **57/57** canonical table names and mandatory starter fields verified in a **published, operator-refreshed metadata snapshot** | Not an audit of every foreign key, data type, permission or operational workflow |
| **Synthetic cloud test data** | Seeded examples include **8,880 vitals**, **720 cabin CO₂ readings**, **120 sleep sessions**, **24 biological samples**, and **32 laboratory results** | These are *protected, deliberately simulated test rows*; counts published publicly are restricted to approved seed identifiers |
| **Public demonstration feed** | **428 approved synthetic observations**, isolated from protected clinical tables at the recorded database audit | Anon/public mode cannot read or write protected medical records |
| **Dashboard and feature scope** | Seven dashboards, 12 domain views, 47-feature traceability index, five hazards and 12 scenario descriptions | The full 47-feature acceptance matrix is **not yet passed** |
| **Protected examination/laboratory reader** | Role- and mission-checked FastAPI → local SQLite synthetic evidence, with automated tests | Available only to authorized development/test API sessions, not to anonymous judges or as verified cloud clinical reads |
| **Offline and clinical synchronization** | SQLite/outbox architecture and prototype modules exist | Fresh restart/reconnect, exact cloud receipts and deduplication are **not fully verified end to end** |
| **S01–S12 acceptance** | Scenario definitions and local-test reporting exist | **All 12 deployed end-to-end scenarios are not yet verified**; the scenario selector is not a test executor |

See [feature-by-feature coverage](frontend/docs/FEATURE_MATRIX.md), [PDF alignment and gaps](docs/PDF_ALIGNMENT_STATUS.md), [cloud schema and seed reconciliation](docs/MASTERDOCS_CLOUD_RECONCILIATION_20261117.md), and [reviewed clinical-evidence integration](docs/REVIEWED_DRAFT_CLINICAL_EVIDENCE.md).

> **Interpretation of “57/57 verified”:** The published schema inspection established that **the required table names and starter-field names exist**. It does **not** mean that all tables are full, all SQL constraints match MasterDocs, or all 57 business workflows have been implemented. The snapshot is refreshed by a trusted database operator; reloading the browser does not re-inspect protected tables.

## 🏗️ Architecture and data protection

### Public, no-login demonstration — deployed

~~~text
Judge's browser
  React + TypeScript + Vite  (Vercel)
          │ GET only /api/v1/public/*
          ▼
  Python FastAPI              (Railway)
          │ validated, restricted requests
          ▼
  Supabase PostgreSQL
     ├── approved synthetic observation feed
     └── approved 57-table schema metadata snapshot

  Protected medical tables remain behind authorization/RLS.
~~~

### Separate protected, local-first research architecture

~~~text
Authorized mission client
    → FastAPI validation + clinical/role controls
    → onboard/local encrypted SQLite
    → outbox / sync queue
    → authorized Supabase ingestion and receipts (integration gate pending)
~~~

The public feed and schema catalog are **different publication surfaces**. Neither publishes confidential check-ins, raw clinical table contents, privileged keys, medical diagnoses or user tokens. Public read access does **not** grant INSERT/UPDATE/DELETE. The new local clinical-evidence endpoints require authorization and are not replacements for the private cloud data pipeline.

The interface intentionally distinguishes missing data, stale/unsupported observations, synthetic values, and unverified clinical reports. It does **not** automatically diagnose clots, osteoporosis, SANS, infection or radiation illness; prescribe treatment; clear EVA; or actuate spacecraft. No arbitrary research threshold is presented as NASA-approved medical policy.

## 🧪 MasterDocs acceptance and scientific integrity

The 15 November 2026 MasterDocs defines six release gates:

| Gate | Acceptance goal | Present assessment |
| --- | --- | --- |
| G1 · Database & identity | Clean migrations, 57 tables, relationships, RLS, deterministic seed | Table/field snapshot and synthetic seeds checked; clean-room migration, all FK/RLS assertions pending |
| G2 · Offline platform | Six SQLite operational tables, encryption, durable data across restart | Prototype code exists; full restart/reconnect proof pending |
| G3 · Core monitoring | Validated ingest, baseline, symptoms, rules, alerts/incidents | Partial implementation; S01–S04/S10/S11 full proof pending |
| G4 · Dashboards | Seven navigable views, evidence provenance, role protection | Routes and UI built; protected actions/role acceptance not fully certified |
| G5 · Research modules | Exams, assays, radiation, microbiology and review workflows | Selected synthetic examples and protected local readers; full source-aware acceptance pending |
| G6 · Sync & final demo | Cloud receipts, idempotence, audit and reproducible S01–S12 | Not yet proven end to end |

**Research principles used in the prototype:** D-dimer does not diagnose a clot; Doppler/ultrasound findings preserve vessel side; OCT preserves eye/region; bone DXA is pre/postflight only unless a valid in-flight source exists; dose measurements require compatible quantity, units and time interval; confidential behavioral check-ins require restricted access. Missing evidence is **unavailable**, not “normal.”

Our local scenario test report deliberately says **`live_supabase_verified=false`** and **`all_deployed_scenarios_verified=false`**. A passing unit-test suite cannot substitute for an actual cloud-receipt demonstration.

## 🗂️ Source code and reproducibility

| Location | What it contains |
| --- | --- |
| [`frontend/`](frontend/) | Vite/React dashboards, 3D body explorer, domain pages, integration client and public Data Tables |
| [`backend/`](backend/) | FastAPI, local SQLite, role checks, data validation, integration routes and tests |
| [`supabase/`](supabase/) | Cloud SQL migrations, explicit synthetic seeds, metadata-refresh SQL and preflight queries |
| [`docs/`](docs/) | Requirement crosswalk, PDF alignment, architecture, deployment and verification notes |
| [`archive/`](archive/) | Historical/alternate teammate implementations; **not used for deployment** |

**Default release branch: `main`.** Keep the other `draft` branch for its unreviewed fresh-schema SQL proposal; do not execute that 903-line script on the current Supabase project. PRs [#10](https://github.com/LAYMmMz/TeamRocket/pull/10), [#11](https://github.com/LAYMmMz/TeamRocket/pull/11), [#12](https://github.com/LAYMmMz/TeamRocket/pull/12) and [#13](https://github.com/LAYMmMz/TeamRocket/pull/13) are merged into `main`.

### Run the frontend locally

Requirements: Node.js 24 (or the repository-compatible version), npm, and a running FastAPI service for connected public data.

~~~bash
git clone https://github.com/LAYMmMz/TeamRocket.git
cd TeamRocket/frontend
npm ci
npm run check:scope
npm run build
npm run dev
~~~

For the database-connected frontend, create an untracked `frontend/.env.local`:

~~~ini
VITE_DATA_MODE=public
VITE_API_BASE_URL=/api/v1
~~~

The local Vite dev proxy forwards `/api` to FastAPI at `127.0.0.1:8000`; see [backend/README.md](backend/README.md) for the backend environment and local run commands. `VITE_DATA_MODE=demo` uses browser fixtures **instead of** database data. `VITE_DATA_MODE=api` requires an authorized API identity; it is not the public judge mode.

### Automated checks

~~~bash
# From frontend/
npm run check:scope
npm run build
# CI starts Vite and installs Chromium before running:
npm run test:database-ui

# From backend/
python -m pip install -r requirements.txt
python -m unittest discover -s tests -t .
python -m scripts.masterdocs_scenario_report
~~~

[GitHub Actions](https://github.com/LAYMmMz/TeamRocket/actions) runs the frontend checks, frontend/API integration tests and the **local-only** scenario report. Local passes are evidence of automated code behavior—not confirmation of all cloud medical workflows.

### Deployment overview

**Vercel:** project [teamrocket-rocketpulse](https://vercel.com/laymmmzs-projects/teamrocket-rocketpulse), connected to `main`, framework **Vite**, root directory **`frontend`**, build `npm run build`, output `dist`. Production environment: `VITE_DATA_MODE=public`, `VITE_API_BASE_URL=/api/v1`.

**Railway:** the `teamrocket-fastapi` service builds the repository's [`backend/Dockerfile`](backend/Dockerfile). The public Vercel hostname forwards `/api` via [`frontend/vercel.json`](frontend/vercel.json). Railway may use an explicitly pinned reviewed commit: after backend changes, redeploy the intended commit and verify `/api/health` before calling a release complete.

**Supabase:** `TeamRocketV2Database` stores PostgreSQL cloud tables and isolated public synthetic data under row-level security. Keep secrets/JWTs and any privileged database keys **server-side only**. Do not place `service_role` or private tokens in `VITE_*` variables. The [published schema snapshot procedure](docs/LIVE_SUPABASE_DATA_TABLES.md) is operator-refreshed; it is not a real-time inspector of protected clinical rows.

### Quick verification URLs

- [Production frontend](https://teamrocket-rocketpulse.vercel.app/command)
- [Backend health through Vercel](https://teamrocket-rocketpulse.vercel.app/api/health)
- [Synthetic command API](https://teamrocket-rocketpulse.vercel.app/api/v1/public/missions/DEMO-01/command?astronaut_id=CREW-01)
- [Approved 57-table schema API](https://teamrocket-rocketpulse.vercel.app/api/v1/public/schema/catalog)
- [Read-only Data Tables page](https://teamrocket-rocketpulse.vercel.app/data-model)

For an unauthorized visitor, a protected clinical endpoint should deny access (401/403). Do **not** submit sensitive medical information or try anonymous writes to prove connectivity.

## 📚 Scope and credits

**Primary project specification:** *NASA Astronaut Health Monitoring System — Final Development MasterDocs*, **15 November 2026** (team-provided, 13-page implementation source of truth). Sections 0–15 establish architecture, 12 domains, five hazards, the 57-table inventory, six SQLite tables, synthetic seed, S01–S12, seven dashboards, F01–F47, API contracts and G1–G6 acceptance.

The MasterDocs references original/integrated MasterDocs, the 2026 physiology/technology update, and NASA/CSA publications as **supporting research**. Their inclusion does not mean RocketPulse has official NASA endorsement, permission to use private clinical catalogs, or approval of clinical thresholds. Any operational rule would require a documented source, revision, reviewer and approval.

Built by **TeamRocket** for the **NASA Space Apps Challenge**. The published prototype uses **synthetic research data only**.

---

**[Launch RocketPulse](https://teamrocket-rocketpulse.vercel.app/command)** · **[Browse GitHub source](https://github.com/LAYMmMz/TeamRocket)** · **[View coverage and limitations](frontend/docs/FEATURE_MATRIX.md)**
