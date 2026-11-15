# QA / release limitations

## Manifest validation performed

`node scripts/check-scope.mjs` verifies 47 feature IDs, 7 views, 12 domains, 57 canonical cloud tables, 6 onboard tables, 12 scenario definitions and 5 hazards plus cross-references. It **does not** validate live backend behavior.

A TypeScript transpilation syntax check is possible in the build environment; however, full `npm install`, `npm run build`, and browser runtime validation require the dependency registry and could not be run in the provided offline environment. Do not describe this project as production-ready or all 47 features implemented.

## Source-backed seed targets, not all generated in frontend

| Seed dataset | Source target | Actual frontend mock implementation |
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
