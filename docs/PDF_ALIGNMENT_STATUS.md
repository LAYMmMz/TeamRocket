# PDF alignment and database-read verification

Reviewed against Final Development MasterDocs, 15 November 2026, sections 0–15.

## Implemented corrections

- Public mode is the default. Browser fixtures require explicit `VITE_DATA_MODE=demo`.
- Dashboard domain panels, 3D body explorer, domain history and feature-detail observations use the selected crew's FastAPI reads. No fixture fallback on request failure. Old crew results are hidden immediately during selection changes, and stale domain requests are aborted.
- Public reads remain restricted to approved synthetic Supabase samples. Private clinical tables are not exposed. A schema catalog is explicitly distinct from a live database inspection.
- Undefined `IMMUNE_INDEX`, `BONE_INDEX`, `VASCULAR_INDEX`, `OCT_INDEX` and `CULTURE_INDEX` values are excluded by both the API and public UI. The feed does not contain the assay, anatomical region, laterality or protocol evidence needed to replace them with legitimate examinations.
- Public API checks metric/domain/unit consistency and finite values. A domain without supported data returns an empty list, not fabricated normality.
- Observation timestamps come from records. Missing baselines, device state, private alert counts and examination state are not described as measured zero/normal. Trend charts use separate units.
- Public scenario descriptions are reference material; the selector no longer implies backend execution. Private writes and synchronization remain authorized operations.
- The canonical `/api/vitals` and `/api/reports/summary` routers are registered. Previously, legacy routes intercepted these requests. The legacy `metric_code` vital POST is now `/api/clinical/vitals`; canonical `/api/vitals` takes `metric`. Legacy ECG/batch/baseline routes are unchanged.
- Feature pages now describe the specific read capability or missing evidence instead of applying a blanket SCAFFOLD label. No feature is declared fully accepted merely because it has a page.

## Verification

- Full backend discovery: 174 tests, 4 skipped, no failures after routing fixes.
- TypeScript and production frontend build pass. Vite reports the existing large main bundle warning.
- Scope check: 47 features, seven views, 12 domains, five hazards, 57 logical cloud tables, six offline tables and 12 scenarios.
- Added Playwright checks for connected dashboard rendering, crew-switch isolation, unsupported index filtering, empty/error states, feature reads, scenario boundaries and disabled public writes. Local execution was blocked by the environment's Chromium socket restriction; CI runs this suite with installed Chromium.
- Existing live public API was read during the audit: immune returned an undefined `IMMUNE_INDEX` sample, confirming the need for filtering. This is not evidence that the updated backend has deployed.
- Direct Supabase inspection returned `You do not have permission to perform this action`; no database schema or data was modified in this change.

## Remaining acceptance blockers

The PDF defines a larger system than the public numeric sample feed. Completing these requires authorized database access and records/contracts, not additional frontend labels:

1. Verify all 57 physical cloud tables, constraints, RLS, source metadata, deterministic clean migrations and six SQLite tables against the PDF. Existing repository migrations explicitly do not bootstrap the entire cloud project.
2. Publish approved synthetic structured exam/lab/radiation/environment records with assay method, side/eye/site, dose quantity, intervals, review and provenance. Do not use invented indices to fill absent clinical data.
3. Demonstrate authorized symptom/incident/procedure and record import workflows with immutable evidence, approved versioned rules and persisted acknowledgments.
4. Verify S01–S12 against the actual deployed system, including offline restart, sync receipts, replay deduplication, expired rule handling and confidential-record denial. Passing local tests is not a deployed cloud acceptance certificate.
5. Replace research-only references only when authoritative datasets and reviewer approvals exist; never invent IMM/CLiFF catalogs, medical rules or treatment instructions.

Public read-only access is intentional. Removing clinical authorization to make judge controls writable would conflict with the PDF.

## Feature-by-feature scope

“Connected read” means the page can request available observations, not that all behaviors of that feature are complete. Database emptiness and API errors remain visible. Every feature still needs the PDF's complete acceptance evidence.

| ID | PDF feature | Current capability / next evidence |
| --- | --- | --- |
| F01 | Mission and astronaut management | Related domain read where available; specialized records/workflow evidence required |
| F02 | User roles and clinical data permissions | Authorized workflow; not executable in public mode |
| F03 | Device-agnostic sensor and report import | Related domain read where available; specialized records/workflow evidence required |
| F04 | Measurement validation and provenance | Related domain read where available; specialized records/workflow evidence required |
| F05 | Personal health baseline management | Related domain read where available; specialized records/workflow evidence required |
| F06 | Shared symptom reporting | Authorized workflow; not executable in public mode |
| F07 | Configurable, versioned clinical alert engine | Authorized workflow; not executable in public mode |
| F08 | Central medical incident handling | Authorized workflow; not executable in public mode |
| F09 | Approved procedure and recommendation library | Related domain read where available; specialized records/workflow evidence required |
| F10 | Mission-aware examination scheduling | Related domain read where available; specialized records/workflow evidence required |
| F11 | Local storage and offline operation | Authorized workflow; not executable in public mode |
| F12 | Ground synchronization and audit history | Authorized workflow; not executable in public mode |
| F13 | Cardiovascular vital signs and ECG reporting | Connected observation read; full workflow acceptance required |
| F14 | Respiratory and oxygenation monitoring | Connected observation read; full workflow acceptance required |
| F15 | Vascular ultrasound and D-dimer result review | Related domain read where available; specialized records/workflow evidence required |
| F16 | Gravity-adaptation and vestibular assessments | Related domain read where available; specialized records/workflow evidence required |
| F17 | Cognitive and reaction-time assessments | Related domain read where available; specialized records/workflow evidence required |
| F18 | Aerobic fitness and muscle assessments | Related domain read where available; specialized records/workflow evidence required |
| F19 | Exercise and physical workload tracking | Connected observation read; full workflow acceptance required |
| F20 | Bone-density and recovery examinations | Related domain read where available; specialized records/workflow evidence required |
| F21 | SANS/OCT, visual acuity and fundoscopy | Related domain read where available; specialized records/workflow evidence required |
| F22 | Sleep and circadian monitoring | Connected observation read; full workflow acceptance required |
| F23 | Nutrition, hydration and fluid balance logs | Related domain read where available; specialized records/workflow evidence required |
| F24 | Behavioral-health check-ins | Related domain read where available; specialized records/workflow evidence required |
| F25 | Personal and area radiation dosimetry | Connected observation read; full workflow acceptance required |
| F26 | Solar particle event and radiation incident monitoring | Related domain read where available; specialized records/workflow evidence required |
| F27 | Cabin atmosphere and pressure monitoring | Connected observation read; full workflow acceptance required |
| F28 | Light and noise monitoring | Related domain read where available; specialized records/workflow evidence required |
| F29 | Environmental microbial sampling | Related domain read where available; specialized records/workflow evidence required |
| F30 | Water, air, food and surface test results | Related domain read where available; specialized records/workflow evidence required |
| F31 | Spacesuit microbial hygiene records where available | Related domain read where available; specialized records/workflow evidence required |
| F32 | Blood, saliva, urine and other sample management | Related domain read where available; specialized records/workflow evidence required |
| F33 | Onboard and Earth-laboratory test imports | Related domain read where available; specialized records/workflow evidence required |
| F34 | Immune and viral biomarker result histories | Related domain read where available; specialized records/workflow evidence required |
| F35 | Sequencing and multi-omics dataset records where available | Related domain read where available; specialized records/workflow evidence required |
| F36 | Medical inventory and consumables | Related domain read where available; specialized records/workflow evidence required |
| F37 | Versioned condition-reference catalog | Related domain read where available; specialized records/workflow evidence required |
| F38 | Emergency clinical notification and acknowledgment | Authorized workflow; not executable in public mode |
| F39 | Offline crew guidance access | Authorized workflow; not executable in public mode |
| F40 | Mission Medical Command dashboard | Connected observation read; full workflow acceptance required |
| F41 | Individual Astronaut Health dashboard | Connected observation read; full workflow acceptance required |
| F42 | Clinical Examinations and Recovery dashboard | Related domain read where available; specialized records/workflow evidence required |
| F43 | Radiation and Environment dashboard | Connected observation read; full workflow acceptance required |
| F44 | Laboratory and Immune Health dashboard | Related domain read where available; specialized records/workflow evidence required |
| F45 | Crew Self-Assessment dashboard | Related domain read where available; specialized records/workflow evidence required |
| F46 | Ground Medical Review dashboard | Authorized workflow; not executable in public mode |
| F47 | Synthetic end-to-end mission demonstration | End-to-end offline replay not verified |

## Reproduce checks

```bash
cd backend
python -m pip install -r requirements.txt
python -m unittest discover -s tests -t .
cd ../frontend
npm ci
npm run check:scope
npm run build
npx playwright install chromium
npm run dev
# In another terminal in frontend/:
npm run test:database-ui
```

For local database reads, run FastAPI on port 8000 with its server-only Supabase configuration. Vite proxies `/api` to it. Hosted Vercel uses the existing Railway rewrite. The browser test uses controlled API responses to test UI behavior; it does not write cloud data or prove cloud deployment.
