# TeamRocket — Close remaining Dev1 / Dev2 cloud gaps (additive patch)

This is a **source-code patch**, not a completed production deployment. It fixes the known Dev1 sync receipt bug, and adds a **durable, transaction-coupled local Dev2 clinical outbox**. It provides a separate **Supabase clinical evidence staging RPC** and RLS, subject to Database Team review.

**It does not replace the 57 normalized clinical tables, grant medical clearance, bypass mission membership, or prove live cloud connectivity.** You still must deploy the migration, create authenticated test membership, and run post-integration acceptance tests.

## 0. Safety

1. Stop the running server with `Ctrl+C`. Back up the entire current `Developer1_Backend/backend` folder and especially **`data/offline.db`, `data/offline.db.key`, `data/dev2_clinical.db` and its WAL/SHM**, and any existing `astronaut_health.db`.
2. **Do not delete/copy over/replace SQLite database files**, encryption keys or `.env` files. This patch contains no database files or secrets.
3. Verify that your friend merge was installed (`app/core/dev1_bridge.py`, `app/models/dev2_models.py`, and `app/dev2_friend_attach.py` exist). The installer refuses to run without them.
4. The new migration MUST be reviewed and deployed to a **disposable Supabase test project first**. Never test using production crew data.

## 1. Apply source patch

Extract the ZIP and copy the following into `Developer1_Backend/backend`:

- `install_cloud_completion.py`
- The entire `app/cloud_completion/` folder (including `outbox.py`)
- Optional `supabase/` and `tests/` and `verify_patch.py` files

**IMPORTANT:** The installer expects `app/cloud_completion/outbox.py` to exist in the ZIP's source folder, but it must NOT already exist in your backend yet. Therefore, the safest method is to extract this ZIP directly into your **backend parent**, leaving a new folder `TeamRocket_Cloud_Completion_Patch` alongside `backend`, then copy only `install_cloud_completion.py` into `backend`, and run it with `--source` pointing to the extracted folder. See the updated command below.

```powershell
cd "C:\Users\Serge\Documents\VSCODE\python\NASA\Developer1_Backend\backend"
python install_cloud_completion.py --source "..\TeamRocket_Cloud_Completion_Patch"
```

It validates three pinned existing code anchors before changing anything, backs up originals under `_cloud_completion_source_backup_...`, and never modifies database contents directly.

## 2. Supabase migration for Dev2 clinical evidence

Ask the Database Team to review and apply `supabase/20261116_03_clinical_sync_records.sql` to the **same reviewed test project** as the `20261115_02` migration.

- Requires existing `public.mission_members`, `public.sync_audit_log`, and real `auth.users`.
- Adds `public.clinical_sync_records` (RLS-protected, mission member read-only; additional clinician-only reads for sensitive clinical domains).
- Adds `public.ingest_clinical_sync_event(p_event jsonb)`. Supports `kind=clinical_record`; idempotent retry returns `duplicate_ok`; divergent replay returns `conflict` (and a durable audit row).
- Uses a **generic clinical evidence envelope** so all 28 domain model categories can arrive in Supabase without pretending the normalized domain-table mapping is finished. This is a transitional cloud storage contract and **must be approved by your Database Team**.
- Do not run the SQL against production until the Database Team completes RLS/privacy checks, verifies the migration on the test project, and signs off.

## 3. Configure the backend (local/private configuration only)

When the database migration and mission membership are ready, configure your existing Dev1 variables (`SYNC_RPC_URL`, `SYNC_ACCESS_TOKEN`, `SUPABASE_ANON_KEY`) with your test environment. The patch routes `clinical_record` to `ingest_clinical_sync_event` automatically if the old RPC URL ends in `/ingest_sync_event`, or you can set:

```powershell
$env:SYNC_CLINICAL_RPC_URL="https://YOUR-TEST-PROJECT.supabase.co/rest/v1/rpc/ingest_clinical_sync_event"
```

Use an **authenticated short-lived test-user JWT** assigned to the mission in `public.mission_members`; never commit or share credentials. NOTE: an old JWT will expire; cloud worker must refresh identity appropriately before production use.

**No existing measurements or old Dev2 rows are bulk-migrated by the patch.** It captures new changes. To backfill historical demo records you will need a separately reviewed, opt-in batch importer rather than an automatic destructive re-seed.

## 4. Verify

First run the included static/isolated unit tests:

```powershell
python verify_patch.py
```

Run your prepared full backend verification suite, using the disposable test project, after integration:

```powershell
python run_post_integration.py --local
python run_post_integration.py --full --ack-live-test-writes
```

Expected cloud evidence after creating one fresh Dev2 record: one durable `teamrocket_clinical_cloud_outbox` row (`enqueued`), one encrypted `clinical_record` item in Dev1 `offline.db`, one Supabase `public.clinical_sync_records` entry, and a valid receipt with `status='ingested'` or `'duplicate_ok'`. The original Dev1 `measurement` still appears in `public.health_logs`.

For automated clinical tests, point the previously generated `clinical_cases.json` at **`public.clinical_sync_records`**, verifying `resource_type`, `source_id`, and `record` values. Also verify that unauthorized mission users cannot read any row, and non-medical users cannot read sensitive records.

## 5. Remaining blockers before the entire backend can be called finished

1. Database Team must fix the **existing** `health_logs` `ON CONFLICT (id) DO NOTHING` false-success possibility and validate the migration checksum; the patch does not overwrite their migration.
2. Database Team must confirm that `mission_members.user_id` refers to a real `auth.users` identity.
3. End-to-end live sync, RLS and privacy must pass in a test Supabase project.
4. Complete the **normalized mapping to dedicated clinical cloud tables** if the project requirements demand those tables, rather than just generic evidence staging.
5. Confirm signed JWT refresh and retry behavior for long-duration offline operations.
6. Validate the user's real merged installation with `run_post_integration.py` including S01–S12 and frontend acceptance.

**Do not interpret the installation success message as test success.**
