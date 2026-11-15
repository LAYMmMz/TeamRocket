# Database SQL status

- migrations/: the Database branch's forward RPC scripts, preserved unchanged.
- rollbacks/: manual DROP FUNCTION scripts; deliberately kept outside forward migrations.
- queries/: read-only inspection query.
- legacy/schema.sql: original partial schema with broad read policies; reference only, not approved for deployment.

This is NOT a reproducible 57-table database baseline. The legacy schema creates only eight tables and uses names/columns that differ from the MasterDocs. The RPC migrations reference prerequisites such as mission_members, sync_receipts, sync_audit_log, astronauts.crew_code and extra health_logs columns that the supplied legacy schema does not fully create.

The clinical_records patch is a generic sync destination, not a replacement for the 57 canonical logical tables. The backend patch package contains another clinical SQL variant under archive/backend-patches; do not apply both variants as though they were sequential migrations.

Before cloud deployment, reconcile canonical names, write the missing baseline migrations, review role/mission policies, test from an empty development database, and verify event-specific sync receipts. Do not apply rollback scripts during setup. No cloud SQL was executed during repository organization.
