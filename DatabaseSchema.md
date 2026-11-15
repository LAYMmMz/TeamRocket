# NASA Astronaut Health Monitoring — Database Schema & Architecture

**Primary Datastore:** Supabase (PostgreSQL)  
**Compliance Baseline:** MasterDocs Chapter 4 (Section 4.1) & Chapter 5  
**Environment Scope:** Cloud Mission Store (distinct from onboard local SQLite `sync_queue`)

---

## 1. Core Architectural Rules & Governance

* **Immutability & Medical History Protection (Section 5):** Operational and clinical observation tables enforce `ON DELETE RESTRICT` on foreign keys referencing `astronauts` and parent records. Medical records are never cascade-deleted; historical records must be soft-archived if deprecated.
* **Data Provenance & Synthetic Flagging:** All seeded test/simulation records carry `is_synthetic = true` (or explicit provenance inside `audit_context`) to isolate simulation telemetry from live clinical records.
* **Storage & Credential Security:** Large clinical attachments (e.g., sequencing runs, ultrasound imaging, raw ECG waveforms) reside in **Supabase Storage** and are referenced via object paths. Secret service-role keys are strictly excluded from the Next.js frontend bundle; clients use the public `anon` key governed by Row-Level Security (RLS).
* **Environment Ownership (`sync_queue`):** The onboard spacecraft SQLite `sync_queue` manages local offline buffering. The cloud PostgreSQL database tracks ground-bound messages, sync receipts, and ingestion audits separately.

---

## 2. Section 4.1 Mandatory Observation Data Dictionary

Every observation, telemetry, and measurement table implements the following standardized metadata columns:

| Column Name | PostgreSQL Type | Default / Constraint | Description |
| :--- | :--- | :--- | :--- |
| `id` / `event_id` | `uuid` | `PRIMARY KEY`, `gen_random_uuid()` | Unique record / external event identifier |
| `astronaut_id` | `uuid` | `NOT NULL`, `FK -> astronauts(id) ON DELETE RESTRICT` | Subject crew member |
| `mission_id` | `text` / `uuid` | `NOT NULL` | Associated mission identifier |
| `source_device_id` | `text` / `uuid` | Nullable | Hardware sensor or medical device ID |
| `source_type` | `text` | `'Automated Telemetry'` / `'Manual Entry'` | Origin classification of the reading |
| `measured_at` | `timestamptz` | `NOT NULL` | Timestamp when the physiological/sensor event occurred |
| `received_at` | `timestamptz` | `timezone('utc', now())` | Timestamp when ingested into cloud PostgreSQL |
| `original_value` | `numeric` | Nullable (where JSONB applies) | Raw uncalibrated/unconverted reading value |
| `original_unit` | `text` | Nullable | Unit of the raw reading (e.g., `bpm`, `mSv`, `kcal`, `minutes`) |
| `normalized_value` | `numeric` | Nullable | Standardized SI/clinical unit value (populated when valid) |
| `normalized_unit` | `text` | Nullable | Standardized unit corresponding to `normalized_value` |
| `quality_status` | `text` | `'Unknown'` | Signal/data quality (`Unknown` is treated as neither normal nor verified) |
| `verification_status` | `text` | `'Unverified'` | Automated or device-level verification state |
| `clinical_review_state` | `text` | `'Unreviewed'` | Clinician sign-off workflow state (`Unreviewed`, `Reviewed`, `Flagged`) |
| `audit_context` | `jsonb` | Nullable | Provenance metadata, import batch IDs, and `is_synthetic` flags |

---

## 3. Core Tables & Domain Inventory

### A. Crew, Baselines & Assignments
* **`missions`**: Mission metadata, timelines, and operational parameters.
* **`astronauts`**: Crew profiles and demographic identifiers (`ON DELETE RESTRICT` enforced across all dependent clinical logs).
* **`mission_crew`**: Junction mapping `astronauts` to `missions` with role assignments.
* **`user_role_assignments`**: Maps platform users to RBAC roles (`crew`, `crew_medical_officer`, `ground_clinician`, `mission_operator`, `administrator`) and optional mission scopes.
* **`device_assignments`**: Links hardware sensors/wearables (`devices`) to an `astronaut_id` or habitat location.
* **`health_baselines`**: Reference benchmark values (`metric_code`, `baseline_value`, `measurement_method`, `validity`) used by the alert engine to detect physiological deviations.

### B. Telemetry & Physiological Observations *(Section 4.1 Compliant)*
* **`health_logs`**: Time-series vital signs and readiness metrics (`gravity_level`, `systolic_blood_pressure`, `diastolic_blood_pressure`, `heart_rate`, `nausea_level`, `readiness_status`) plus Section 4.1 dictionary columns.
* **`sleep_sessions`**: Sleep tracking logs (`start_at`, `end_at`, `original_value` mapped to duration in `minutes`, `source_type`).
* **`nutrition_logs`**: Dietary intake tracking (`measured_at`, `intake_details` JSONB macro breakdown, `original_value` in `kcal`).
* **`fluid_balance_logs`**: Hydration tracking (`intake`, `output`, `period_start`, `period_end`, `original_value` net balance, `original_unit`).
* **`behavioral_checkins`**: Psychological and cognitive check-ins (strictly isolated via RLS from unprivileged dashboards).

### C. Radiation & Habitat Environment *(Section 4.1 Compliant)*
* **`personal_dose_records`**: Crew-worn dosimeter radiation exposure logs (`original_value`, `original_unit`, cumulative/interval dose tracking).
* **`radiation_area_records`**: Habitat compartment radiation sensor logs.
* **`environmental_readings`**: Cabin atmosphere, temperature, pressure, CO₂, and humidity telemetry.

### D. Clinical Samples & Specialized Examinations
* **`biological_samples` & `clinical_sample_chain`**: Sample collection metadata and chain-of-custody audit trail.
* **`laboratory_results`**: Lab assay outputs referencing `biological_samples`.
* **`sequencing_runs`**: Genomic/microbiome runs referencing `biological_samples` and Supabase Storage object paths.
* **`environmental_samples` & `environmental_lab_results`**: Surface/water swab samples and corresponding lab analyses.
* **`ocular_assessments` & `ocular_results`**: Eye exam sessions and region/side-specific results (enforces same eye/method for longitudinal comparisons).
* **`bone_scans` & `bone_density_results`**: DEXA/bone mineral density scans and anatomical region results.
* **`ultrasound_exams`**: Links `astronaut_id`, `mission_id`, examiner ID, and Supabase Storage imaging paths.

### E. Alerts, Rules, Procedures & Audits
* **`alert_rules`**: Versioned clinical and environmental threshold definitions.
* **`health_alerts`**: Triggered warnings referencing `alert_rules` version and `astronaut_id` or habitat location.
* **`alert_events` & `alert_evidence`**: Immutable state-change log and explicit typed links to the specific observation records that triggered an alert.
* **`approved_procedures` & `recommendation_records`**: Standard medical countermeasures linked to active `health_alerts`.
* **`incidents` & `incident_events`**: Mission medical/environmental incident tracking and immutable event timelines.
* **`source_files`, `sync_receipts`, & `audit_logs`**: Ingestion tracking, file provenance, and denied-access security logs.

---

## 4. Frontend Integration Guidelines (Next.js)

1. **Client Initialization:** Use `@supabase/supabase-js` with `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` in `.env.local`.
2. **Quality Filtering:** When rendering vital sign charts or calculating baseline deviations, always check `quality_status` and `clinical_review_state`—never display `'Unknown'` quality readings as verified normal data.
3. **Timestamps:** Always order time-series queries by `measured_at` (when the event happened) rather than `created_at` or `received_at` (when the packet reached Earth).