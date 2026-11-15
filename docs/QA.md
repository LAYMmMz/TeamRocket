# QA status

## Automated checks

- TypeScript strict compilation and Vite production build.
- 16 Vitest tests: 57-table/47-feature coverage, four-crew baseline, workout context, missing SpO2/severe symptom, correlated CO2 alert, unreviewed D-dimer, side specificity, stale dose/quantity separation, no in-flight BMD, microbial method/unit, serialized demo queue persistence, expired guidance, denied-access audit, role scoping, form validation, distinct new emergencies.

These tests do not prove P0 backend acceptance. No backend was available.

## Manual browser checks

Use the checklist below for every demo deployment:

- Mission command and four crew cards render without clipped primary content.
- S03 opens a critical alert with absent SpO2, versioned demo rule and incident identity.
- Acknowledgment changes alert state but does not resolve the incident.
- Individual profile renders the interactive Three.js suit and personal vitals.
- Administrator can navigate all seven required dashboards; crew sees own record; mission operator cannot access confidential check-ins.
- Source records retain method, unit, measured time and simulation status.
- Narrow layouts stack cards and expose navigation via the menu.
- Sound requires explicit enabling; warning/critical alarms stop after acknowledgment or mute. This is a browser foreground demo only, not guaranteed emergency delivery.

## Limitations and required integration tests

No real clinical data or thresholds; all fixture values are synthetic and not clinically validated. No full-volume backend seed, API server, Supabase migration/RLS proof, SQLite commit/encryption, authenticated offline grant, idempotent replay guarantee, signed attachment retrieval, background push notifications, actual medical catalog, clinical algorithm, diagnosis, prescription or EVA clearance. P2 unsupported inputs remain source-pending. Real authentication/session refresh and complete DTO runtime validation are integration work.

Browser-local demo receipts are not cloud receipts. Repeated scenario runs create distinct new incidents; production event retransmission must deduplicate by immutable event ID in the backend. Medical review notes in mock mode are display demonstrations, not trusted clinician authorizations.

## Observed browser verification (15 November 2026)

All seven required dashboard routes and Data & coverage were opened successfully. S03 evidence and acknowledgment were verified; missing SpO2 stayed unavailable. The cloud browser has WebGL disabled, so the model uses the included Three.js SVG compatibility renderer; the full suit was visually verified. GPU rendering still needs a local WebGL-capable browser check. Mobile CSS breakpoints were implemented, but a separate narrow-viewport browser test was not performed.
