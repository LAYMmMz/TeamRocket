# MasterDocs verification gates — what is and is not proved

**Source of truth:** NASA Astronaut Health Monitoring Final Development MasterDocs (2026-11-15), §§3–14. The specification requires **47 software features**, **57 logical cloud tables**, **6 offline SQLite tables**, and **12 scenarios**; it does not specify 47 clinical trials.

## Status (17 November 2026)

- **Clinical exam/lab prototype:** the existing Dev2 local SQLite models support side-aware vascular findings, OCT per eye, pre/post DXA by region, sample chain of custody, assay-method evidence and sequencing QC. The new `/api/v1/clinical/examinations/{astronaut_id}` and `/api/v1/clinical/laboratory/{astronaut_id}` routes expose *only synthetic local records* to a mission-authorized flight surgeon/admin in development/test mode. They are not part of the anonymous public feed or production cloud tables. The frontend shows the records in authenticated API mode only.
- **Cloud schema:** Supabase access through the connected project was denied, so the existence of the required 57 actual tables, FKs, policies and seeded records is **NOT VERIFIED**. The SQL in `supabase/queries/masterdocs_57_table_preflight.sql` is read-only. Run it in the correct Supabase project as an authorized database owner and export the 57-row audit. It verifies *only* presence of required tables/columns and the RLS-enabled flag, not valid constraints or RLS effectiveness.
- **Scenarios:** Local unit tests cover some S01–S12 outcomes, but S04 and S05 acceptance tests in `backend/tests/test_teamrocket_acceptance.py` are explicitly skipped. The existing fixture generator writes descriptions, not live events. S10 uses an in-memory receipt transport rather than actual cloud sync. This means **all 12 deployed end-to-end scenarios are NOT VERIFIED**.

## How to reproduce local checks

From `backend`:
```sh
python -m unittest discover -s tests -t .
python -m scripts.masterdocs_scenario_report
```

The second command emits machine-readable JSON with statuses `LOCAL_TEST_PASSED_CLOUD_UNVERIFIED`, `SKIPPED_LOCAL_TEST`, `FAILED_LOCAL_TEST`, and `MISSING_TEST`. It deliberately emits `live_supabase_verified: false` regardless of local success.

## What must happen before COMPLETE may be claimed

1. **G1 cloud schema:** Run the preflight against `TeamRocketV2Database`; reconcile all 57 tables with actual column types, UUID mapping, FKs, timestamps, unique event IDs, RLS policies, role grants, storage permissions, time indexes and clean migrations. Protect clinical tables from anonymous reads and writes.
2. **G2 offline:** Validate all six physical SQLite tables; create a serious-symptom event while disconnected, restart the backend, reconnect, and confirm exactly one matching Supabase receipt and no duplicate alert.
3. **G3–G5 clinical:** Provide approved synthetic *structured* exam/lab/radiation/environment records with method/unit/side/eye/region/sample provenance. Prove clinician authorization, quality/review fields, restricted behavioral check-ins, approved rule versioning and protected procedure acknowledgments.
4. **G6 scenarios:** Execute S01 through S12 on a nonproduction staging deployment with dedicated fictional crew and test credentials. Record execution timestamps, Git SHA, anonymized event IDs, screenshots or JSON, destination receipt IDs, 403 audit evidence, and a test report for each scenario. S04 and S05 must be implemented and tested, not skipped. S10 must use actual cloud receipts, not `MemoryReceiptTransport`.
5. **Security:** Never add unreviewed read policies to `public` clinical tables or expose service-role keys to Vite. Never mark synthetic research thresholds NASA-approved.

The README and feature registry must only claim **COMPLETE** when code, data, UI/API, test, authorization and deployment evidence actually exist per MasterDocs p.13.
