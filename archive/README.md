# Preserved alternatives and historical packages

These files contain unique teammate work and were retained rather than discarded.

- frontend-flight-health/: the full alternate frontend branch, including its own docs, lockfile and tests. It is not the Vercel frontend selected by the root README. Its nested workflow is preserved as a reference and is not an active repository workflow.
- backend-patches/: earlier installer packages and their tests. The active backend already contains the V2 outbox. Do not rerun installers unless intentionally reviewing/reapplying an integration.
- database-prototype/: the standalone Database branch API, retained separately from the integrated backend.
- database-client/: original Supabase query examples; they are not wired into the active Vite app.

Historical instructions may assume their original package directory layout. Use the root README for the active project. The earlier flight-health PR is superseded as a layout proposal, but its unique implementation remains here.
