# TeamRocket Unified Supabase Cloud Patch V2

**Source baseline:** GitHub Database branch commit `65eda22201be61defa289b3f7f1d114291022320` (unified `public.ingest_sync_event` RPC, `public.health_logs` and `public.clinical_records`). This ZIP is a **backend source patch only**. Do **not** run the previous `20261116_03_clinical_sync_records.sql` (it expects an obsolete separate RPC/table).

## What this does

- Keeps the existing FastAPI, Dev1 encrypted SQLite, Dev2 clinical SQLite, and all Dev2 endpoints.
- Ensures only `ingested`/`duplicate_ok` receipts can mark Dev1 queued items synced.
- Stages newly created/modified Dev2 SQLAlchemy records in a transaction-coupled outbox then into Dev1's encrypted sync queue, with event kinds accepted by the new Database SQL.
- Sends **both Dev1 and Dev2** to the **single existing** `.../rpc/ingest_sync_event` endpoint.
- Maps 28 Dev2 model tables into the 8 supported domain kinds (`vital_sign`, `symptom`, `radiation`, `environment`, `wellness`, `examination`, `laboratory_result`, `report`). The 28th `report` kind is not currently produced by these SQLAlchemy tables; report endpoints might need a separate queued `report` write if cloud reports are essential to your demo.
- **Does not** re-upload existing Dev2 historical records or fix obsolete `clinical_record` events already in the Dev1 queue. New events use the unified RPC.

## Before you run anything

1. Stop the backend (`Ctrl+C`) and back up the entire `Developer1_Backend/backend` folder. In particular, preserve `data/*.db`, `data/*.db.key`, `data/*.db-wal`, `data/*.db-shm`, and `.env` / `.env.local`.
2. Extract this ZIP into the `Developer1_Backend` folder so `TeamRocket_Unified_Cloud_Patch_V2` is **beside** `backend`.
3. Open **PowerShell inside `Developer1_Backend/backend`**. Use your local `py -3.13` command if the copied `.venv` is broken.
4. This installer checks whether the prior cloud patch is already installed. It backs up source files and refuses an unexpected/partially patched state. It never opens or deletes a database.

## Install (Windows PowerShell)

```powershell
# You are in Developer1_Backend\backend
py -3.13 "..\TeamRocket_Unified_Cloud_Patch_V2\install_unified_cloud.py" --source "..\TeamRocket_Unified_Cloud_Patch_V2"
```

**Important:** The installer uses its current working directory to find your backend; don't run it from another directory. In an isolated source checkout, inspect the generated backup folder `_unified_cloud_source_backup_*` if you need to restore.

After a successful install, run the **local isolated tests from the extracted ZIP**:

```powershell
py -3.13 "..\TeamRocket_Unified_Cloud_Patch_V2\tests\test_unified_mapping.py"
```

## Configure your already-known Supabase project link

Do **not** paste your secret key into ChatGPT/Messenger or put it in React. The key needed by a **user-JWT-based** sync worker is the **publishable/anon key**, plus the **access token from a real Supabase Auth test user**. A Supabase `sb_secret_...` key is privileged and is NOT a user JWT; do not substitute it for `SYNC_ACCESS_TOKEN`.

For a **disposable test Supabase project**, in the same PowerShell window:

```powershell
$env:SUPABASE_URL="https://YOUR-PROJECT.supabase.co"
$env:SUPABASE_ANON_KEY="YOUR-PUBLISHABLE-OR-LEGACY-ANON-KEY"
$env:SYNC_RPC_URL="$env:SUPABASE_URL/rest/v1/rpc/ingest_sync_event"
```

Have your Database Team confirm that **both** `20261115_02_ingest_sync_event_rpc.sql` and `20261116_03_clinical_sync_rpc.sql` were applied to that exact project, `public.mission_members` contains the test account's `auth.users.id` for the correct mission, and `public.astronauts` contains the test crew code.

Obtain the short-lived authenticated test-user JWT in the same terminal (the helper prompts for password and never prints the token):

```powershell
& "..\TeamRocket_Unified_Cloud_Patch_V2\login_supabase_test.ps1" -Email "YOUR_TEST_USER_EMAIL"
```

You can then run your existing backend startup command **from the same terminal**. The JWT expires; for a longer-running demo, an authenticated token-refresh mechanism is still needed. Do not use an admin/service-role key to evade authorization.

### Mission and astronaut IDs

- Events preserve source `mission_id`. Many Dev2 entities default to `DEMO-01`; verify that your test Auth account is a member of **DEMO-01**. If only assigned `DEMO-02`, ask Database Team to add an authorized membership for `DEMO-01` or create your demo records for `DEMO-02` where supported.
- `astronaut_id` must be an existing Supabase astronaut UUID or `crew_code` accepted by the Database RPC, e.g. `TEST-CREW-01`. If your local Dev2 uses different crew IDs, seed those codes in `public.astronauts`.
- Environmental, area radiation, samples, and other shared records sometimes lack an astronaut ID, but the Database RPC demands one. For a **synthetic demo only**, if you explicitly want such records grouped under a designated synthetic astronaut, set `$env:SYNC_DEFAULT_ASTRONAUT_CODE="TEST-CREW-01"`. **This is a demo attribution convenience, not a clinically valid person association.** Without it, these outbox items remain pending with an error instead of being mislabeled.

## Validation / meaning of success

1. `py -3.13 dev.py` (or your usual FastAPI startup) must start without errors.
2. Create one NEW Dev1 measurement and one NEW Dev2 symptom through your backend, using an authorized mission and an astronaut code in Supabase.
3. Trigger existing Dev1 sync (or the background worker). Inspect the original encrypted queue statuses and the real Supabase `health_logs`, `clinical_records`, `sync_receipts`. Check matching IDs and values.
4. Verify retry/duplicate and conflict response do not falsely mark queue items synced.
5. Run S01-S12 and your existing automated acceptance suite. **A successful installer message is not proof of working cloud sync.**

The V2 patch only modifies Python **source** files; the first subsequent start/clinical write may create the new outbox table in your local clinical SQLite database. It does NOT run migrations against Supabase.

### Known limitations / don't hide failures

- Existing Dev2 rows are not backfilled; existing queued `clinical_record` events from patch V1 remain incompatible, and must be handled separately (they should fail visibly, not be dropped).
- Not every Dev2 table contains an astronaut ID or source mission. Records without source identification may require explicit synthetic-demo mapping or Database Team seed setup.
- A few reporting endpoints may generate reports without writing the SQLAlchemy clinical tables; those are not cloud-queued by this patch.
- Dev2 SQLite remains offline-first. **Do not set `DATABASE_URL` or `DEV2_DATABASE_URL` to Supabase Postgres**. The SQLAlchemy Dev2 model schema is NOT the Supabase schema.
- Do not commit `.env`, secrets, private keys, local medical data, or `data/*.db` files to GitHub.
