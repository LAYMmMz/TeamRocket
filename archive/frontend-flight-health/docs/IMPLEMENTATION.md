# Implementation sequence for the team

## 1. Frontend developer: run the mock interface now

Use the README quick start. Keep all simulation flags visible. Use administrator demo role to inspect the full frontend; role changes affect presentation only. Browser demo data is stored under `teamrocket-demo-v1`, so refresh retains fictional reports. Reset demo clears this state to the baseline.

Use the simulator for presentations. S02 contextualizes workout HR; S03 raises a severe symptom incident without inventing SpO2; S04 correlates cabin CO2 and symptoms; S05–S09 demonstrate clinical-review boundaries; S10 simulates disconnect/reconnect; S11 blocks expired guidance; S12 shows a denied-access audit. The S12 button is a scenario demonstration, not proof of server authorization.

## 2. Database developer: freeze canonical names before coding integrations

Reconcile `DatabaseSchema.md` using SCHEMA_RECONCILIATION.md. Implement all 57 tables in `/supabase/migrations/*.sql`, six onboard tables in `/backend/offline/migrations/*.sql`, foreign keys/time indexes/unique event IDs, no destructive cascades, RLS and private Storage policies. Create `/docs/data_dictionary.csv` and ERD. Test clean migration, forbidden access and deterministic seed counts.

Use UUIDs internally; CREW-01..04 and DEMO-01 are display codes. Preserve timestamps in UTC. Maintain quantity/unit, eye/side/region, method, verification, source, synthetic provenance and measured/received distinctions. Never interpret null as normal.

## 3. Backend developer: implement the agreed contract

Implement Pydantic schemas, JWT verification and authorized mission/crew scope. Add the four adapter routes in API_CONTRACT.md first. GET dashboard should aggregate canonical records without creating dashboard-specific clinical tables. The proposed DTO is a convenience projection; expand it with complete typed evidence, timestamps and pagination as needed.

The shared Python engine, not JavaScript, owns operational alerts. Persist immutable local events before attempting remote sync. Every rule needs version/approval/source/applicability; expired definitions cannot authorize guidance. Acknowledgment does not mean incident resolution.

Implement the other PDF families incrementally: `/auth`, `/missions`, `/astronauts`, `/devices`, `/measurements`, `/samples`, `/examinations`, `/radiation`, `/environment`, `/alerts`, `/incidents`, `/procedures`, `/inventory`, `/reports`, `/sync`.

Publish versioned OpenAPI and regenerate client types. Use stable idempotency keys across retries, event receipts, conflict audit and explicit success states. Add pagination/cursors and timestamped chart series when leaving the small demo dataset.

## 4. Integrate authentication and confidentiality

Replace the developer access-token panel with Supabase Auth sign-in and session renewal. Keep service-role keys server-side. Enforce backend scopes and Supabase RLS even if a user edits browser state. Scope crew to their own records; operator views exclude confidential medical/behavioral content. Return no private notes in general audit responses. Expired grants must block privileged offline operations.

The browser demo stores fictional private notes in localStorage; it is deliberately not a secure clinical store. Never migrate this mechanism to actual medical data. Use the protected onboard FastAPI/SQLite architecture specified in the PDF.

## 5. Switch on API mode and test failure behavior

Set `VITE_DATA_MODE=api` and `VITE_API_BASE_URL` in `.env.local`; restart Vite. In the account panel supply a development Supabase JWT temporarily. Check own-crew scoping, 401/403/409/422 failures, server-created alerts, mutation acknowledgments, and reconnect behavior. Do not expose real data through the prototype.

Mutation success must come from the server. Check that a failed write shows an error and leaves no false success indicator. Complete clinician-reviewed source references before enabling any actual operational-style warning.

## 6. Deploy the frontend on Vercel

Import the GitHub repository; select `frontend` as Root Directory and Vite as framework. Build `npm run build`; output `dist`; install `npm ci`. Begin with `VITE_DATA_MODE=mock`. Deploy the feature branch as preview or merge the reviewed PR to main. Change environment variables and redeploy when the backend is ready. FastAPI CORS must explicitly permit the Vercel origin.

Vercel hosts the static frontend. Onboard SQLite must live with a persistent local backend; do not place a mutable onboard database in the static build. Cloud Postgres/Auth/Storage stay in Supabase. Vercel's frontend being online does not prove cloud receipts or offline medical operations are implemented.

## 7. Team QA acceptance gates

G1: migrations/RLS/seed; G2: encrypted or protected SQLite and cached expiring grants; G3: shared rules and S01–S04/S10/S11; G4: all seven dashboards, accessible labels and API role checks; G5: method-aware exam/lab/environment imports and S05–S09; G6: reconnect, duplicate receipt replay, full mission demonstration. The provided frontend tests cover only client contracts and demo guardrails, not these backend gates.
