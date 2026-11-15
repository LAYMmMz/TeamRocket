# Repository consolidation record

## Source branch snapshots

| Branch | Original head |
| --- | --- |
| Database | `deb6a5a460bda66a9d0a330339b5962d9cc07861` |
| backend | `d30366875ed84fe284090c53fb743ae2303af710` |
| chore/organize-project-structure | `42d15b212b556c43de4873d139267ed3eaafb3a0` |
| frontend/flight-health | `5f1c71ead20faafc5c1cb81826165a4a5ebfcce9` |
| main | `51384c016e93e44412d280a4fa016a39c6dadafc` |

The consolidation commit has all five source heads as parents. Existing branch names are retained and fast-forwarded to this shared layout; no force push or history deletion is required. Alternative implementations remain under archive and are not activated automatically. PR #1 and PR #2 are superseded by this consolidation.

## Preserved file mapping

| Source branch | Original path | Destination |
| --- | --- | --- |
| Database | `Downloads/backend/.gitignore` | `archive/database-prototype/.gitignore` |
| Database | `Downloads/backend/database.py` | `archive/database-prototype/database.py` |
| Database | `Downloads/backend/docs/id_mappings.csv` | `docs/database/id_mappings.csv` |
| Database | `Downloads/backend/docs/rls_tests.md` | `docs/database/rls_tests.md` |
| Database | `Downloads/backend/docs/schema_export_full.csv` | `docs/database/schema_export_full.csv` |
| Database | `Downloads/backend/docs/schema_handoff.json` | `docs/database/schema_handoff.json` |
| Database | `Downloads/backend/docs/sync_receipt_contract.md` | `docs/database/sync_receipt_contract.md` |
| Database | `Downloads/backend/main.py` | `archive/database-prototype/main.py` |
| Database | `Downloads/backend/mapping.md` | `archive/database-prototype/mapping.md` |
| Database | `Downloads/backend/supabase/migrations/20261115_02_ingest_sync_event_rpc.sql` | `supabase/migrations/20261115_02_ingest_sync_event_rpc.sql` |
| Database | `Downloads/backend/supabase/migrations/20261115_02_rollback.sql` | `supabase/rollbacks/20261115_02_rollback.sql` |
| Database | `Downloads/backend/supabase/migrations/20261116_03_clinical_sync_rpc.sql` | `supabase/migrations/20261116_03_clinical_sync_rpc.sql` |
| Database | `Downloads/backend/supabase/migrations/20261116_03_rollback.sql` | `supabase/rollbacks/20261116_03_rollback.sql` |
| Database | `Downloads/backend/sync.py` | `archive/database-prototype/sync.py` |
| Database | `Downloads/schema.sql` | `supabase/legacy/schema.sql` |
| Database | `lib/Instructions.md` | `archive/database-client/Instructions.md` |
| Database | `lib/Supbasequeries.js` | `archive/database-client/Supbasequeries.js` |
| Database | `test` | `supabase/queries/inspect_schema.sql` |
| backend | `Developer1_Backend/.gitignore` | `archive/backend-patches/.gitignore` |
| backend | `Developer1_Backend/README.md` | `docs/backend-original-overview.md` |
| backend | `Developer1_Backend/TeamRocket_Cloud_Completion_Patch/README_FIRST.md` | `archive/backend-patches/TeamRocket_Cloud_Completion_Patch/README_FIRST.md` |
| backend | `Developer1_Backend/TeamRocket_Cloud_Completion_Patch/app/cloud_completion/outbox.py` | `archive/backend-patches/TeamRocket_Cloud_Completion_Patch/app/cloud_completion/outbox.py` |
| backend | `Developer1_Backend/TeamRocket_Cloud_Completion_Patch/supabase/20261116_03_clinical_sync_records.sql` | `archive/backend-patches/TeamRocket_Cloud_Completion_Patch/supabase/20261116_03_clinical_sync_records.sql` |
| backend | `Developer1_Backend/TeamRocket_Cloud_Completion_Patch/tests/test_cloud_sql_static.py` | `archive/backend-patches/TeamRocket_Cloud_Completion_Patch/tests/test_cloud_sql_static.py` |
| backend | `Developer1_Backend/TeamRocket_Cloud_Completion_Patch/tests/test_installer_isolated.py` | `archive/backend-patches/TeamRocket_Cloud_Completion_Patch/tests/test_installer_isolated.py` |
| backend | `Developer1_Backend/TeamRocket_Cloud_Completion_Patch/tests/test_outbox_isolated.py` | `archive/backend-patches/TeamRocket_Cloud_Completion_Patch/tests/test_outbox_isolated.py` |
| backend | `Developer1_Backend/TeamRocket_Unified_Cloud_Patch_V2/README_FIRST.md` | `archive/backend-patches/TeamRocket_Unified_Cloud_Patch_V2/README_FIRST.md` |
| backend | `Developer1_Backend/TeamRocket_Unified_Cloud_Patch_V2/app/cloud_completion/outbox.py` | `archive/backend-patches/TeamRocket_Unified_Cloud_Patch_V2/app/cloud_completion/outbox.py` |
| backend | `Developer1_Backend/TeamRocket_Unified_Cloud_Patch_V2/install_unified_cloud.py` | `archive/backend-patches/TeamRocket_Unified_Cloud_Patch_V2/install_unified_cloud.py` |
| backend | `Developer1_Backend/TeamRocket_Unified_Cloud_Patch_V2/login_supabase_test.ps1` | `archive/backend-patches/TeamRocket_Unified_Cloud_Patch_V2/login_supabase_test.ps1` |
| backend | `Developer1_Backend/TeamRocket_Unified_Cloud_Patch_V2/tests/test_unified_mapping.py` | `archive/backend-patches/TeamRocket_Unified_Cloud_Patch_V2/tests/test_unified_mapping.py` |
| backend | `Developer1_Backend/backend/.gitignore` | `backend/.gitignore` |
| backend | `Developer1_Backend/backend/README.md` | `backend/README.md` |
| backend | `Developer1_Backend/backend/app/__init__.py` | `backend/app/__init__.py` |
| backend | `Developer1_Backend/backend/app/alerts/__init__.py` | `backend/app/alerts/__init__.py` |
| backend | `Developer1_Backend/backend/app/alerts/models.py` | `backend/app/alerts/models.py` |
| backend | `Developer1_Backend/backend/app/alerts/router.py` | `backend/app/alerts/router.py` |
| backend | `Developer1_Backend/backend/app/alerts/service.py` | `backend/app/alerts/service.py` |
| backend | `Developer1_Backend/backend/app/auth/__init__.py` | `backend/app/auth/__init__.py` |
| backend | `Developer1_Backend/backend/app/auth/dependencies.py` | `backend/app/auth/dependencies.py` |
| backend | `Developer1_Backend/backend/app/auth/router.py` | `backend/app/auth/router.py` |
| backend | `Developer1_Backend/backend/app/cloud_completion/__init__.py` | `backend/app/cloud_completion/__init__.py` |
| backend | `Developer1_Backend/backend/app/cloud_completion/outbox.py` | `backend/app/cloud_completion/outbox.py` |
| backend | `Developer1_Backend/backend/app/config.py` | `backend/app/config.py` |
| backend | `Developer1_Backend/backend/app/core/__init__.py` | `backend/app/core/__init__.py` |
| backend | `Developer1_Backend/backend/app/core/body_limit.py` | `backend/app/core/body_limit.py` |
| backend | `Developer1_Backend/backend/app/core/config.py` | `backend/app/core/config.py` |
| backend | `Developer1_Backend/backend/app/core/db.py` | `backend/app/core/db.py` |
| backend | `Developer1_Backend/backend/app/core/dependencies.py` | `backend/app/core/dependencies.py` |
| backend | `Developer1_Backend/backend/app/core/dev1_bridge.py` | `backend/app/core/dev1_bridge.py` |
| backend | `Developer1_Backend/backend/app/core/errors.py` | `backend/app/core/errors.py` |
| backend | `Developer1_Backend/backend/app/core/models.py` | `backend/app/core/models.py` |
| backend | `Developer1_Backend/backend/app/db/__init__.py` | `backend/app/db/__init__.py` |
| backend | `Developer1_Backend/backend/app/db/session.py` | `backend/app/db/session.py` |
| backend | `Developer1_Backend/backend/app/dev2_friend_attach.py` | `backend/app/dev2_friend_attach.py` |
| backend | `Developer1_Backend/backend/app/domain2/__init__.py` | `backend/app/domain2/__init__.py` |
| backend | `Developer1_Backend/backend/app/domain2/analysis.py` | `backend/app/domain2/analysis.py` |
| backend | `Developer1_Backend/backend/app/domain2/baselines.py` | `backend/app/domain2/baselines.py` |
| backend | `Developer1_Backend/backend/app/domain2/clinical_logic.py` | `backend/app/domain2/clinical_logic.py` |
| backend | `Developer1_Backend/backend/app/domain2/contracts.py` | `backend/app/domain2/contracts.py` |
| backend | `Developer1_Backend/backend/app/domain2/dashboards.py` | `backend/app/domain2/dashboards.py` |
| backend | `Developer1_Backend/backend/app/domain2/reports.py` | `backend/app/domain2/reports.py` |
| backend | `Developer1_Backend/backend/app/domain2/router.py` | `backend/app/domain2/router.py` |
| backend | `Developer1_Backend/backend/app/domain2/vitals.py` | `backend/app/domain2/vitals.py` |
| backend | `Developer1_Backend/backend/app/environment/__init__.py` | `backend/app/environment/__init__.py` |
| backend | `Developer1_Backend/backend/app/environment/router.py` | `backend/app/environment/router.py` |
| backend | `Developer1_Backend/backend/app/environment/service.py` | `backend/app/environment/service.py` |
| backend | `Developer1_Backend/backend/app/examinations/__init__.py` | `backend/app/examinations/__init__.py` |
| backend | `Developer1_Backend/backend/app/examinations/router.py` | `backend/app/examinations/router.py` |
| backend | `Developer1_Backend/backend/app/examinations/service.py` | `backend/app/examinations/service.py` |
| backend | `Developer1_Backend/backend/app/foundation/__init__.py` | `backend/app/foundation/__init__.py` |
| backend | `Developer1_Backend/backend/app/foundation/models.py` | `backend/app/foundation/models.py` |
| backend | `Developer1_Backend/backend/app/foundation/router.py` | `backend/app/foundation/router.py` |
| backend | `Developer1_Backend/backend/app/incidents/__init__.py` | `backend/app/incidents/__init__.py` |
| backend | `Developer1_Backend/backend/app/incidents/models.py` | `backend/app/incidents/models.py` |
| backend | `Developer1_Backend/backend/app/incidents/router.py` | `backend/app/incidents/router.py` |
| backend | `Developer1_Backend/backend/app/incidents/service.py` | `backend/app/incidents/service.py` |
| backend | `Developer1_Backend/backend/app/integrations/__init__.py` | `backend/app/integrations/__init__.py` |
| backend | `Developer1_Backend/backend/app/integrations/router.py` | `backend/app/integrations/router.py` |
| backend | `Developer1_Backend/backend/app/integrations/schema.py` | `backend/app/integrations/schema.py` |
| backend | `Developer1_Backend/backend/app/inventory/__init__.py` | `backend/app/inventory/__init__.py` |
| backend | `Developer1_Backend/backend/app/inventory/models.py` | `backend/app/inventory/models.py` |
| backend | `Developer1_Backend/backend/app/inventory/router.py` | `backend/app/inventory/router.py` |
| backend | `Developer1_Backend/backend/app/inventory/service.py` | `backend/app/inventory/service.py` |
| backend | `Developer1_Backend/backend/app/main.py` | `backend/app/main.py` |
| backend | `Developer1_Backend/backend/app/measurements/__init__.py` | `backend/app/measurements/__init__.py` |
| backend | `Developer1_Backend/backend/app/measurements/models.py` | `backend/app/measurements/models.py` |
| backend | `Developer1_Backend/backend/app/measurements/router.py` | `backend/app/measurements/router.py` |
| backend | `Developer1_Backend/backend/app/measurements/service.py` | `backend/app/measurements/service.py` |
| backend | `Developer1_Backend/backend/app/measurements/units.py` | `backend/app/measurements/units.py` |
| backend | `Developer1_Backend/backend/app/models/__init__.py` | `backend/app/models/__init__.py` |
| backend | `Developer1_Backend/backend/app/models/dev2_models.py` | `backend/app/models/dev2_models.py` |
| backend | `Developer1_Backend/backend/app/nasa/__init__.py` | `backend/app/nasa/__init__.py` |
| backend | `Developer1_Backend/backend/app/nasa/router.py` | `backend/app/nasa/router.py` |
| backend | `Developer1_Backend/backend/app/offline/__init__.py` | `backend/app/offline/__init__.py` |
| backend | `Developer1_Backend/backend/app/offline/store.py` | `backend/app/offline/store.py` |
| backend | `Developer1_Backend/backend/app/procedures/__init__.py` | `backend/app/procedures/__init__.py` |
| backend | `Developer1_Backend/backend/app/procedures/models.py` | `backend/app/procedures/models.py` |
| backend | `Developer1_Backend/backend/app/procedures/router.py` | `backend/app/procedures/router.py` |
| backend | `Developer1_Backend/backend/app/procedures/service.py` | `backend/app/procedures/service.py` |
| backend | `Developer1_Backend/backend/app/radiation/__init__.py` | `backend/app/radiation/__init__.py` |
| backend | `Developer1_Backend/backend/app/radiation/router.py` | `backend/app/radiation/router.py` |
| backend | `Developer1_Backend/backend/app/radiation/service.py` | `backend/app/radiation/service.py` |
| backend | `Developer1_Backend/backend/app/reports/__init__.py` | `backend/app/reports/__init__.py` |
| backend | `Developer1_Backend/backend/app/reports/router.py` | `backend/app/reports/router.py` |
| backend | `Developer1_Backend/backend/app/reports/service.py` | `backend/app/reports/service.py` |
| backend | `Developer1_Backend/backend/app/samples/__init__.py` | `backend/app/samples/__init__.py` |
| backend | `Developer1_Backend/backend/app/samples/router.py` | `backend/app/samples/router.py` |
| backend | `Developer1_Backend/backend/app/samples/service.py` | `backend/app/samples/service.py` |
| backend | `Developer1_Backend/backend/app/schemas/__init__.py` | `backend/app/schemas/__init__.py` |
| backend | `Developer1_Backend/backend/app/schemas/dev2_schemas.py` | `backend/app/schemas/dev2_schemas.py` |
| backend | `Developer1_Backend/backend/app/seed/__init__.py` | `backend/app/seed/__init__.py` |
| backend | `Developer1_Backend/backend/app/seed/scenarios.py` | `backend/app/seed/scenarios.py` |
| backend | `Developer1_Backend/backend/app/seed/seed_demo.py` | `backend/app/seed/seed_demo.py` |
| backend | `Developer1_Backend/backend/app/simulation/__init__.py` | `backend/app/simulation/__init__.py` |
| backend | `Developer1_Backend/backend/app/simulation/router.py` | `backend/app/simulation/router.py` |
| backend | `Developer1_Backend/backend/app/sync/__init__.py` | `backend/app/sync/__init__.py` |
| backend | `Developer1_Backend/backend/app/sync/router.py` | `backend/app/sync/router.py` |
| backend | `Developer1_Backend/backend/app/sync/worker.py` | `backend/app/sync/worker.py` |
| backend | `Developer1_Backend/backend/app/vitals/__init__.py` | `backend/app/vitals/__init__.py` |
| backend | `Developer1_Backend/backend/app/vitals/router.py` | `backend/app/vitals/router.py` |
| backend | `Developer1_Backend/backend/app/vitals/service.py` | `backend/app/vitals/service.py` |
| backend | `Developer1_Backend/backend/app/wellness/__init__.py` | `backend/app/wellness/__init__.py` |
| backend | `Developer1_Backend/backend/app/wellness/router.py` | `backend/app/wellness/router.py` |
| backend | `Developer1_Backend/backend/app/wellness/service.py` | `backend/app/wellness/service.py` |
| backend | `Developer1_Backend/backend/dev.py` | `backend/dev.py` |
| backend | `Developer1_Backend/backend/install_cloud_completion.py` | `backend/install_cloud_completion.py` |
| backend | `Developer1_Backend/backend/install_dev2_upgrade.py` | `backend/install_dev2_upgrade.py` |
| backend | `Developer1_Backend/backend/install_domain2.py` | `backend/install_domain2.py` |
| backend | `Developer1_Backend/backend/install_friend_merge.py` | `backend/install_friend_merge.py` |
| backend | `Developer1_Backend/backend/install_sqlite_integration.py` | `backend/install_sqlite_integration.py` |
| backend | `Developer1_Backend/backend/install_symptom_sync.py` | `backend/install_symptom_sync.py` |
| backend | `Developer1_Backend/backend/offline/migrations/001_durable_offline.sql` | `backend/offline/migrations/001_durable_offline.sql` |
| backend | `Developer1_Backend/backend/offline/migrations/002_revision_delivery.sql` | `backend/offline/migrations/002_revision_delivery.sql` |
| backend | `Developer1_Backend/backend/requirements.txt` | `backend/requirements.txt` |
| backend | `Developer1_Backend/backend/run_dev2_tests.py` | `backend/run_dev2_tests.py` |
| backend | `Developer1_Backend/backend/run_final.py` | `backend/run_final.py` |
| backend | `Developer1_Backend/backend/run_teamrocket_tests.py` | `backend/run_teamrocket_tests.py` |
| backend | `Developer1_Backend/backend/scripts/__init__.py` | `backend/scripts/__init__.py` |
| backend | `Developer1_Backend/backend/scripts/schema_audit.py` | `backend/scripts/schema_audit.py` |
| backend | `Developer1_Backend/backend/scripts/seed_demo.py` | `backend/scripts/seed_demo.py` |
| backend | `Developer1_Backend/backend/team_sqlite.py` | `backend/team_sqlite.py` |
| backend | `Developer1_Backend/backend/team_sqlite_bridge.py` | `backend/team_sqlite_bridge.py` |
| backend | `Developer1_Backend/backend/team_sqlite_integration.py` | `backend/team_sqlite_integration.py` |
| backend | `Developer1_Backend/backend/tests/__init__.py` | `backend/tests/__init__.py` |
| backend | `Developer1_Backend/backend/tests/test_dev2_api.py` | `backend/tests/test_dev2_api.py` |
| backend | `Developer1_Backend/backend/tests/test_dev2_upgrade.py` | `backend/tests/test_dev2_upgrade.py` |
| backend | `Developer1_Backend/backend/tests/test_domain_contracts.py` | `backend/tests/test_domain_contracts.py` |
| backend | `Developer1_Backend/backend/tests/test_schema_audit.py` | `backend/tests/test_schema_audit.py` |
| backend | `Developer1_Backend/backend/tests/test_teamrocket_acceptance.py` | `backend/tests/test_teamrocket_acceptance.py` |
| backend | `Developer1_Backend/backend/verify_friend_merge.py` | `backend/verify_friend_merge.py` |
| backend | `Developer1_Backend/backend/verify_friend_merge_old.py` | `backend/verify_friend_merge_old.py` |
| backend | `Developer1_Backend/backend/verify_patch.py` | `backend/verify_patch.py` |
| backend | `Developer1_Backend/docs/schema-handoff.json` | `docs/schema-handoff.json` |
| chore/organize-project-structure | `database/docs/DatabaseSchema.md` | `database/docs/DatabaseSchema.md` |
| chore/organize-project-structure | `frontend/.env.example` | `frontend/.env.example` |
| chore/organize-project-structure | `frontend/.gitignore` | `frontend/.gitignore` |
| chore/organize-project-structure | `frontend/README.md` | `frontend/README.md` |
| chore/organize-project-structure | `frontend/docs/BACKEND_HANDOFF.md` | `frontend/docs/BACKEND_HANDOFF.md` |
| chore/organize-project-structure | `frontend/docs/DATABASE_MAP.md` | `frontend/docs/DATABASE_MAP.md` |
| chore/organize-project-structure | `frontend/docs/FEATURE_MATRIX.md` | `frontend/docs/FEATURE_MATRIX.md` |
| chore/organize-project-structure | `frontend/docs/QA_AND_SCOPE.md` | `frontend/docs/QA_AND_SCOPE.md` |
| chore/organize-project-structure | `frontend/index.html` | `frontend/index.html` |
| chore/organize-project-structure | `frontend/package-lock.json` | `frontend/package-lock.json` |
| chore/organize-project-structure | `frontend/package.json` | `frontend/package.json` |
| chore/organize-project-structure | `frontend/preview.html` | `frontend/preview.html` |
| chore/organize-project-structure | `frontend/public/images/earth-horizon-background.jpg` | `frontend/public/images/earth-horizon-background.jpg` |
| chore/organize-project-structure | `frontend/public/models/astronaut-jungle-jim.fbx` | `frontend/public/models/astronaut-jungle-jim.fbx` |
| chore/organize-project-structure | `frontend/public/models/crew-escape-suit.glb` | `frontend/public/models/crew-escape-suit.glb` |
| chore/organize-project-structure | `frontend/scripts/check-scope.mjs` | `frontend/scripts/check-scope.mjs` |
| chore/organize-project-structure | `frontend/scripts/generate-spec.py` | `frontend/scripts/generate-spec.py` |
| chore/organize-project-structure | `frontend/src/App.tsx` | `frontend/src/App.tsx` |
| chore/organize-project-structure | `frontend/src/app/MissionContext.tsx` | `frontend/src/app/MissionContext.tsx` |
| chore/organize-project-structure | `frontend/src/app/labels.ts` | `frontend/src/app/labels.ts` |
| chore/organize-project-structure | `frontend/src/components/AstronautScene.tsx` | `frontend/src/components/AstronautScene.tsx` |
| chore/organize-project-structure | `frontend/src/components/Charts.tsx` | `frontend/src/components/Charts.tsx` |
| chore/organize-project-structure | `frontend/src/components/Icons.tsx` | `frontend/src/components/Icons.tsx` |
| chore/organize-project-structure | `frontend/src/components/UI.tsx` | `frontend/src/components/UI.tsx` |
| chore/organize-project-structure | `frontend/src/components/astronaut-scene.css` | `frontend/src/components/astronaut-scene.css` |
| chore/organize-project-structure | `frontend/src/data/masterdocs.json` | `frontend/src/data/masterdocs.json` |
| chore/organize-project-structure | `frontend/src/layout-theme.css` | `frontend/src/layout-theme.css` |
| chore/organize-project-structure | `frontend/src/lib/api.ts` | `frontend/src/lib/api.ts` |
| chore/organize-project-structure | `frontend/src/lib/demo.ts` | `frontend/src/lib/demo.ts` |
| chore/organize-project-structure | `frontend/src/lib/types.ts` | `frontend/src/lib/types.ts` |
| chore/organize-project-structure | `frontend/src/main.tsx` | `frontend/src/main.tsx` |
| chore/organize-project-structure | `frontend/src/pages/Dashboards.tsx` | `frontend/src/pages/Dashboards.tsx` |
| chore/organize-project-structure | `frontend/src/pages/DataIntake.tsx` | `frontend/src/pages/DataIntake.tsx` |
| chore/organize-project-structure | `frontend/src/pages/Operations.tsx` | `frontend/src/pages/Operations.tsx` |
| chore/organize-project-structure | `frontend/src/pages/Traceability.tsx` | `frontend/src/pages/Traceability.tsx` |
| chore/organize-project-structure | `frontend/src/styles.css` | `frontend/src/styles.css` |
| chore/organize-project-structure | `frontend/tsconfig.json` | `frontend/tsconfig.json` |
| chore/organize-project-structure | `frontend/vercel.json` | `frontend/vercel.json` |
| chore/organize-project-structure | `frontend/vite.config.ts` | `frontend/vite.config.ts` |
| frontend/flight-health | `.github/workflows/frontend.yml` | `archive/frontend-flight-health/.github/workflows/frontend.yml` |
| frontend/flight-health | `.gitignore` | `archive/frontend-flight-health/.gitignore` |
| frontend/flight-health | `README.md` | `archive/frontend-flight-health/README.md` |
| frontend/flight-health | `docs/API_CONTRACT.md` | `archive/frontend-flight-health/docs/API_CONTRACT.md` |
| frontend/flight-health | `docs/IMPLEMENTATION.md` | `archive/frontend-flight-health/docs/IMPLEMENTATION.md` |
| frontend/flight-health | `docs/QA.md` | `archive/frontend-flight-health/docs/QA.md` |
| frontend/flight-health | `docs/SCHEMA_RECONCILIATION.md` | `archive/frontend-flight-health/docs/SCHEMA_RECONCILIATION.md` |
| frontend/flight-health | `docs/TRACEABILITY.md` | `archive/frontend-flight-health/docs/TRACEABILITY.md` |
| frontend/flight-health | `frontend/.env.example` | `archive/frontend-flight-health/frontend/.env.example` |
| frontend/flight-health | `frontend/index.html` | `archive/frontend-flight-health/frontend/index.html` |
| frontend/flight-health | `frontend/package-lock.json` | `archive/frontend-flight-health/frontend/package-lock.json` |
| frontend/flight-health | `frontend/package.json` | `archive/frontend-flight-health/frontend/package.json` |
| frontend/flight-health | `frontend/src/App.tsx` | `archive/frontend-flight-health/frontend/src/App.tsx` |
| frontend/flight-health | `frontend/src/Astronaut.tsx` | `archive/frontend-flight-health/frontend/src/Astronaut.tsx` |
| frontend/flight-health | `frontend/src/catalog.json` | `archive/frontend-flight-health/frontend/src/catalog.json` |
| frontend/flight-health | `frontend/src/main.tsx` | `archive/frontend-flight-health/frontend/src/main.tsx` |
| frontend/flight-health | `frontend/src/safety.test.ts` | `archive/frontend-flight-health/frontend/src/safety.test.ts` |
| frontend/flight-health | `frontend/src/seed.ts` | `archive/frontend-flight-health/frontend/src/seed.ts` |
| frontend/flight-health | `frontend/src/service.ts` | `archive/frontend-flight-health/frontend/src/service.ts` |
| frontend/flight-health | `frontend/src/styles.css` | `archive/frontend-flight-health/frontend/src/styles.css` |
| frontend/flight-health | `frontend/src/types.ts` | `archive/frontend-flight-health/frontend/src/types.ts` |
| frontend/flight-health | `frontend/tsconfig.json` | `archive/frontend-flight-health/frontend/tsconfig.json` |
| frontend/flight-health | `frontend/vercel.json` | `archive/frontend-flight-health/frontend/vercel.json` |
| frontend/flight-health | `frontend/vite.config.ts` | `archive/frontend-flight-health/frontend/vite.config.ts` |

## Excluded files

Files below are removed from current branch trees, not erased from historical commits. Local runtime data is not source code; recover any needed local records from your existing private working copy before using a newly seeded development database. The committed encryption key must be replaced if it was used beyond disposable demo data.

| Branch | Path | Reason |
| --- | --- | --- |
| Database | `.env.local` | local environment config |
| Database | `DatabaseSchema.md` | identical document retained elsewhere |
| Database | `Downloads/backend/test-results.md` | identical document retained elsewhere |
| backend | `Developer1_Backend/backend/app/__pycache__/__init__.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/__pycache__/main.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/alerts/__pycache__/__init__.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/alerts/__pycache__/models.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/alerts/__pycache__/router.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/auth/__pycache__/__init__.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/auth/__pycache__/dependencies.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/auth/__pycache__/router.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/core/__pycache__/__init__.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/core/__pycache__/body_limit.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/core/__pycache__/config.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/core/__pycache__/dependencies.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/core/__pycache__/errors.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/core/__pycache__/models.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/foundation/__pycache__/__init__.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/foundation/__pycache__/models.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/foundation/__pycache__/router.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/incidents/__pycache__/__init__.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/incidents/__pycache__/models.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/incidents/__pycache__/router.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/incidents/__pycache__/service.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/integrations/__pycache__/__init__.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/integrations/__pycache__/router.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/integrations/__pycache__/schema.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/inventory/__pycache__/__init__.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/inventory/__pycache__/models.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/inventory/__pycache__/router.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/inventory/__pycache__/service.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/main.before_dev2_integration.py.bak` | historical backup retained in Git history |
| backend | `Developer1_Backend/backend/app/main.before_dev2_upgrade.py.bak` | historical backup retained in Git history |
| backend | `Developer1_Backend/backend/app/main.before_friend_merge_20261115_234706.py.bak` | historical backup retained in Git history |
| backend | `Developer1_Backend/backend/app/main.before_team_sqlite_integration.py.bak` | historical backup retained in Git history |
| backend | `Developer1_Backend/backend/app/measurements/__pycache__/__init__.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/measurements/__pycache__/models.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/measurements/__pycache__/router.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/measurements/__pycache__/service.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/measurements/__pycache__/units.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/offline/__pycache__/__init__.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/offline/__pycache__/store.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/procedures/__pycache__/__init__.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/procedures/__pycache__/models.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/procedures/__pycache__/router.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/procedures/__pycache__/service.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/sync/__pycache__/__init__.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/sync/__pycache__/router.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/app/sync/__pycache__/worker.cpython-313.pyc` | generated/duplicate file |
| backend | `Developer1_Backend/backend/data/astronaut_health.db` | local runtime database/key |
| backend | `Developer1_Backend/backend/data/offline.db` | local runtime database/key |
| backend | `Developer1_Backend/backend/data/offline.db.key` | local runtime database/key |
| backend | `Developer1_Backend/backend/dev2_test_report.json` | generated/duplicate file |
| backend | `Developer1_Backend/backend/tests/__init__.py.txt` | generated/duplicate file |
| backend | `README.md` | identical to backend README |
| frontend/flight-health | `DatabaseSchema.md` | identical schema retained elsewhere |
| main | `package-lock.json` | empty orphan lockfile |

## Small maintenance changes

- Root README and ignore rules added; Vercel instructions use frontend.
- Backend README folder/login-helper paths updated.
- SQLAlchemy added to requirements because the current app imports it.
- Frontend specification generator now resolves its output relative to its script.
- Frontend CI adapted from the alternative branch to run the active app's scope check and build.
- Rollback SQL separated from forward migrations; incomplete baseline explicitly documented.

## Validation

Frontend scope check and TypeScript/Vite build passed; public binary assets were preserved by SHA but not rendered locally. Backend suite: 151 checks, 123 PASS, 21 FAIL, 3 ERROR, 4 BLOCKED. No live database was accessed. The cleanup does not resolve the frontend/backend contract mismatch or complete the 57-table migration baseline.
