# QA / release limitations

## Validation performed

`npm run check:scope` verifies 47 feature IDs, 7 views, 12 domains, 57 canonical cloud tables, 6 onboard tables, 12 scenario definitions and 5 hazards plus cross-references. It **does not** validate live backend behavior.

- `npm ci` completed; `npm run build` passed TypeScript and Vite production build. Vite reports the existing large-chunk warning (the main JavaScript chunk is about 1.7 MB before gzip).
- `npm run test:database-ui` passed with Chromium. The controlled API test checks source-accurate public labels, dashboard and explorer reads, crew-switch isolation, unsupported-metric filtering, API error/empty states, read-only controls and scenario boundaries. It does not call or certify the live Supabase service.
- Backend `python -m unittest discover -s tests -t .` passed: 174 tests, 4 skipped.

These checks do **not** make the project production-ready or establish acceptance of all 47 features, live cloud authorization, database migrations, or clinical workflows.

## Source-backed seed targets, not all generated in frontend

| Seed dataset | Source target | Demo-mode fixture implementation |
|---|---:|---|
| Hourly HR / SpO₂ / respiratory rate | 8,640 rows | 8,640 deterministic readings (4 crew × 30 days × 24 hours × 3 metrics) |
| Blood pressure | 240 rows | 240 systolic demo readings (not full BP measurement contract) |
| ECG reports | 4 | Representative fixture label only |
| Vision | 8 ocular results each eye | Representative fixture label only |
| Vascular | 8 side-specific reports | Representative fixture label only |
| Fitness / DXA | 8 assessments / 8 DXA region results | Representative fixture labels only |
| Sleep/exercise | 120 / 120 | Source target counts shown; no 120 specific records seeded |
| Symptoms/check-ins | 24 / 20 | Browser-only symptom form; seed pending |
| Personal radiation | 120 intervals | Representative example only |
| Cabin CO₂ | 720 hourly samples | Target and method coverage; seeding pending |
| Location O₂/pressure | 240 records | Source targets; seeding pending |
| SPE context | 12 samples | S07 scenario only |
| Biological / lab results | 24 / 32 | Target counts; backend seed pending |
| Environmental sample / lab | 12 / 16 | S09 scenario only |
| Sequencing | 4 runs | Metadata representation only |
| Medical catalog/inventory/procedure | 20 / 12 / 8 | Source targets and demo-only records |
| Sync queued/receipts/retry/replay | 30 / 8 / 5 / 4 | S10 visualization only; backend persistence and idempotence pending |

## Critical required acceptance tests

- G1: fresh Supabase migration succeeds; RLS denies forbidden access; deterministic seed counts.
- G2: six SQLite migrations; records survive restart offline; encrypted local persistence and expiring offline grants.
- G3: Pydantic validation, baselines and approved versioned alert rules; S01–S04, S10, S11.
- G4: seven role dashboards navigable **and** backend permissions enforced.
- G5: S05–S09 review workflows, method/side/eye-aware comparisons.
- G6: S10–S12 idempotence, audit and offline reconnect.

**Do not claim these passed until the backend developers execute and capture results.**

## Clinical safeguards

No fabricated sensor values when missing; research-only metrics never produce operational-style clinical warnings; no automatic clot diagnosis; no inferred immune score; no invented BMD during flight; no treatment selection, autonomous EVA clearance, actuation, or unsupported official NASA procedure catalog completeness.
