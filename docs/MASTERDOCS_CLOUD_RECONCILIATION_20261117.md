# MasterDocs schema repair and synthetic cloud seeding — 17 November 2026

## Changes actually applied to the connected Supabase project

Connected project: `TeamRocketV2Database` (`ziecxjoeljxoocixejtz`).

- Existing **57 canonical tables** remain present with RLS enabled. Migration `supabase/migrations/20261117_04_masterdocs_starter_aliases.sql` created compatibility **read-only generated aliases** for 13 missing starter columns in 8 tables. No tables, RLS grants, or existing records were deleted.
- `vital_signs.id` remains an existing `bigint` primary key. Changing it to UUID needs a separate planned backward-compatible migration across client/FK contracts; it is **not fixed** by the aliases.
- Two additive, repeatable, **synthetic-only** seed scripts were run in the connected cloud database: `supabase/seed/masterdocs_synthetic_baseline_20261115.sql` and `supabase/seed/masterdocs_synthetic_clinical_20261115.sql`.
- Seed details: one DEMO-01 mission, four `mission_crew` links, three synthetic locations, eight device records, 8,640 hourly HR/SpO2/RR plus 240 BP readings, 720 CO2 samples, 120 sleep, 120 exercise, 24 biological samples, 32 mock laboratory results, 24 custody records, 8 ocular assessments and 8 ocular results, 8 left/right ultrasound reports, and 8 pre/post-ground-only DXA scans/results.
- The seed is idempotent via stable hash-derived UUIDs or event IDs and `ON CONFLICT DO NOTHING`. Numeric values are fictitious *demonstration inputs*, not validated physiological findings, NASA limits or diagnostic thresholds.
- **These private clinical test records are not available to the anonymous judge dashboard.** The actual `SET LOCAL ROLE anon` preflight returned **0 visible vitals, 0 visible laboratory results and 428 visible approved synthetic public samples**. Although PostgreSQL table-level SELECT grants exist on some protected clinical tables, their RLS policies deny these rows to `anon`; do not infer row accessibility from table grants alone. The separately approved synthetic table and strict public FastAPI API remain unchanged.

## Verification

SQL readback confirmed the count of every table above. See `supabase/queries/masterdocs_seed_preflight.sql` for a deterministic count check. The clinical seed was executed **twice** and all 12 table-count checks remained unchanged and passed, establishing idempotence for this seed script in the existing project. A fresh empty-project migration/re-seed, role-by-role access test and foreign-key/policy audit remain required before declaring G1 passed.

## Still outstanding against the PDF

1. Repair or formally document the legacy bigint `vital_signs` primary key and schema/column compatibility; audit constraints, FK, indexes, and grant/RLS test cases for all tables.
2. Implement validated **private clinical API read/write paths** and ensure the FastAPI local SQLite outbox truly delivers these canonical rows to Supabase with exact-once receipts. The current Railway staging configuration has no configured sync RPC token; cloud seed does not establish pipeline delivery.
3. Expand test fixtures to all source-required datasets (ECG, infection/culture, dose, radiation, exam schedule, environmental assays, procedures, inventory, alerts and audit) using source-specific metadata, reviewed criteria, and explicit synthetic flags.
4. Verify all 12 full scenarios end-to-end, including S10 offline restart/reconnect and deduplication, S11 expired rule denial and S12 confidential access logging. The frontend scenario evidence panel is not scenario execution.
5. Security advisory remains: some tables have RLS enabled without policies (denial by default); some privileged functions warrant review of `EXECUTE` access. Do not grant anonymous clinical-table access merely to populate the judge dashboard.

This branch is **not full MasterDocs acceptance**. Do not merge/deploy merely because seed counts match.
