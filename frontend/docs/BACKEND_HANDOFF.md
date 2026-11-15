# RocketPulse V2 — Python FastAPI / Supabase / SQLite Handoff

## Source-of-truth boundary

The authoritative MasterDocs (15 Nov 2026), sections 0–15, requires a **local-first** architecture:

**Simulated instrument / crew entry / import → FastAPI Pydantic validation → SQLite durable commit → same Python rule engine → React onboard UI → durable sync queue → authenticated Supabase PostgreSQL sync → ground review UI**.

- React never reads SQLite files directly.
- React never receives a Supabase service-role key.
- Backend must enforce role permissions, cached expiring offline grants, audits, and authorized procedures.
- No separate clinical tables for each dashboard. Use the exact 57 logical cloud tables in `masterdocs.json`.
- Physiological and test records carry `event_id`, `is_synthetic`, source, measurement UTC timestamp, received timestamp, unit, quality/verification and reviewer metadata when relevant.
- Records preserve `measured_at`, `local_received_at`, `cloud_received_at`, `clinician_acknowledged_at` as **different** timestamps.

## Concrete proposed API contracts

MasterDocs section 10 names **logical API families, not precise HTTP methods**. Below are proposed routes consumed by this frontend; backend may adapt them through a compatibility adapter and must publish versioned OpenAPI:

| Method | Proposed route | Response | Owner / permission |
|---|---|---|---|
| GET | `/api/v1/missions/DEMO-01/command?astronaut_id=CREW-01` | `CommandSnapshot` | mission medical access |
| GET | `/api/v1/measurements/trends?astronaut_id=CREW-01&hours=24` | `TrendPoint[]` | authorized crew/clinician |
| GET | `/api/v1/reports/domains/cardiorespiratory?astronaut_id=CREW-01` | `CaseRecord[]` | domain permission (use actual id `cardiorespiratory`) |
| POST | `/api/v1/alerts/{alert_id}/acknowledgments` | `Alert` | authorized responder; deduplicated |
| POST | `/api/v1/symptoms` | symptom record / event receipt | crew member or authorized clinician |
| GET | `/api/v1/sync/status` | state, queue depth, last receipt | authorized ground/onboard role |

The frontend adapter is in `src/lib/api.ts`. The displayed per-domain records use normalized `CaseRecord` DTOs; the backend will query/join the relevant canonical tables and return rows with source IDs, labels, quality and provenance.

### Example Pydantic models (adjust to your actual OpenAPI)

```python
from typing import Literal
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID

class Provenance(BaseModel):
    event_id: str
    is_synthetic: bool
    source_type: Literal['synthetic', 'research-only', 'imported']
    measured_at: datetime
    received_at: datetime
    source_device_id: str | None = None
    quality: Literal['ok', 'stale', 'missing', 'review-required']
    verification: Literal['verified-demo', 'review-required', 'unreviewed', 'missing']

class VitalDTO(Provenance):
    id: str
    astronaut_id: str
    metric_code: str
    value: float | None = Field(default=None)
    unit: str
    baseline: float | None = None

class SymptomCreate(BaseModel):
    event_id: UUID
    astronaut_id: str
    symptom_code: str
    severity: Literal['mild', 'moderate', 'serious']
    notes: str = Field(max_length=500)
    is_synthetic: bool = True
```

The full `CommandSnapshot`, `Alert`, `CaseRecord` and `TrendPoint` DTO shapes are declared in `src/lib/types.ts`. Generate TypeScript types from FastAPI OpenAPI for production integration to prevent drift.

## Data sources and display policy

- `/vital_signs`: HR/SpO2/RR with source device, units, baseline, measured/received timestamps, verification and simulation tag. `null` means **MISSING**, never normal.
- `/ecg_records`: waveform in protected Storage, waveform reference in table; no fabricated automatic interpretation.
- `/vascular_ultrasound_results`: preserve `side` (`left` vs `right`), vein, reviewer; D-dimer uses assay method from `laboratory_results`.
- `/ocular_results`: preserve `eye` and protocol from `ocular_assessments`.
- `/bone_density_results`: pre/postflight comparisons only; do not fabricate in-flight BMD.
- `/personal_dose_records` and `/radiation_area_records`: quantity, unit, source, particle species/energy and interval. No universal conversion.
- `/environmental_readings`: location, averaging window and unit; do not compare incomparable CO₂/pressure datasets.
- `/environmental_lab_results`: sample method, CFU denominator and verification; review required.
- `/behavioral_checkins`: confidential notes never sent in unauthorized mission dashboards.
- `/medical_procedures` + `/procedure_steps`: version, source, approval status, expiry. Only currently approved criteria can generate operational-style guidance.
- `/sync_queue` + `/sync_receipts`: immutable event UUID, hash, retry, idempotent receipt, duplicate-replay tests.

## Authentication

- Use Supabase Auth for online identity; frontend registers its **user-scoped access token provider** via `configureAuthTokenProvider(async () => token)` in `src/lib/api.ts`.
- FastAPI checks token signature, expiry, mission grants and permission to every resource, logs denied access and queries Supabase with proper RLS rules or other enforced authorization.
- Onboard offline role grants must be cached, verified, expiring and not reducible to changing UI role dropdown.
- Do not store privileged credentials in `VITE_` environment variables.

## Backend required migrations and seed commands

Required work products: `/supabase/migrations/*.sql`, `/backend/offline/migrations/*.sql`, `/backend/app/seed/seed_demo.py`, `/backend/app/seed/scenarios.py`, `/backend/tests`, `/docs/data_dictionary.csv`, `/docs/erd.pdf`.

The PDF specifies CLI targets to be implemented, **not already present**:

```bash
python -m app.seed.seed_demo --seed 20261115 --reset --profile baseline
python -m app.seed.scenarios --scenario S04 --at 2026-06-15T12:00:00Z
pytest backend/tests
```

Demo-only reset must be blocked outside a marked demo environment. Seed receipts and IDs must be deterministic. The browser scenario selector changes UI data only until connected to the backend runner.

## Definition of done

Seven dashboards navigable, but **none** may claim integrated completion until backend authorization, persistence, seed records, tests, simulated-vs-real source labels, offline restart durability, deduplication receipts, and release documentation pass gates G1–G6.
