# PDF traceability and honest completion status

Source: uploaded Final Development MasterDocs, 15 November 2026, 13 pages. The specification contains requirements and proposed fixtures, not a live dataset. Every canonical table and feature identifier is represented below; this is not a claim that all backend features are implemented.

## Sections and requirements

| PDF section/page | Frontend location | Integration boundary |
|---|---|---|
| 0–1 / p.1: frozen decisions and data flow | README, API adapter, persistent SIMULATED labels | React → FastAPI; SQLite/Supabase server-owned |
| 2 / p.2: twelve domains | Seven primary dashboards and medical resources | Missing/research-only values explicit |
| 3–5 / pp.2–5: database and 57 tables | Data & coverage, catalog.json, map below | No duplicate clinical tables; migrations/RLS backend-owned |
| 6 / p.6: six SQLite tables | Data & coverage, demo queue status | Full offline history/encryption/expiring grants pending backend |
| 7 / pp.6–7: synthetic dataset | Four crew, DEMO-01, 30-point trends, twelve scenario controls | Compact display fixtures; not full-volume seed |
| 8 / p.8: research boundaries | Research & sources; domain record details | CHI/TME/QTL/EVAC/LOCL calculations disabled; no invented IMM/CLiFF/MORD content |
| 9 / p.8: seven dashboards | Seven navigable role views | Browser role guards are a demo; backend must enforce |
| 10 / p.9: endpoint families | API_CONTRACT.md, service.ts | Four proposed operations wired; other families pending |
| 11 / p.9: alert/offline safety | Evidence, demo rule version, acknowledgment, missing values | Shared operational rules engine and exactly-once sync pending |
| 12 / pp.10–12: 47 features | Feature inventory below | Status is frontend-only scope, not full project acceptance |
| 13–15 / pp.12–13: gates, owners, sources | IMPLEMENTATION.md, QA.md | No claim of completed G1–G6 or flight certification |

## Five hazards

| Hazard | Assigned areas |
|---|---|
| Space radiation | Radiation & habitat: personal/area dose, SPE, particle metadata |
| Isolation and confinement | Sleep, confidential self-assessment, fatigue |
| Distance from Earth | Ground review, delay context, demo queue, guidance availability |
| Altered gravity | Adaptation, balance/reaction time, fitness, bone, SANS, vascular/fluid review |
| Hostile/closed environment | Atmosphere/pressure, light/noise, water/air/food/surface samples |

## Canonical table assignments

| Table | Workspace | Mandatory starter fields |
|---|---|---|
| `astronauts` | command | id, crew_code, display_name, status |
| `missions` | command | id, name, mission_type, launch_at, landing_at, phase |
| `mission_crew` | command | mission_id, astronaut_id, crew_role |
| `users` | command | id, authentication_identity, account_status |
| `roles` | command | id, role_name, permissions |
| `user_role_assignments` | command | user_id, role_id, mission_id |
| `devices` | command | id, device_type, model, calibration_status |
| `device_assignments` | command | device_id, astronaut_id, location_id, assigned_at, ended_at |
| `vital_signs` | astronaut | id, astronaut_id, metric_code, value, unit, measured_at, source_device_id, quality |
| `ecg_records` | astronaut | id, astronaut_id, start_at, end_at, waveform_reference, reviewed_interpretation |
| `symptom_reports` | astronaut | id, astronaut_id, symptom_code, severity, onset_at, reported_at, body_location |
| `health_baselines` | astronaut | id, astronaut_id, metric_code, baseline_value, measurement_method, validity |
| `medical_findings` | astronaut | id, astronaut_id, finding_code, interpretation, reviewer_id, reviewed_at |
| `medical_incidents` | command | id, astronaut_id, mission_id, incident_type, priority, status |
| `incident_events` | command | id, incident_id, event_type, actor_id, occurred_at |
| `biological_samples` | laboratory | id, astronaut_id, sample_type, collected_at, source, processing_status |
| `laboratory_results` | laboratory | id, sample_id, test_code, result_value, unit, assay_method, verification |
| `microbial_identifications` | laboratory | id, sample_id, organism, identification_method, result_status |
| `sequencing_runs` | laboratory | id, sample_id, platform, run_quality, data_reference |
| `clinical_sample_chain` | laboratory | id, sample_id, custody_event, responsible_person, occurred_at |
| `vascular_ultrasound_results` | exams | id, astronaut_id, vein, side, flow_pattern, thrombus_finding, reviewed_by |
| `ocular_assessments` | exams | id, astronaut_id, test_type, assessed_at, report_reference |
| `ocular_results` | exams | id, assessment_id, eye, metric_code, value, unit, interpretation |
| `fitness_assessments` | exams | id, astronaut_id, test_type, metric_code, value, protocol, assessed_at |
| `exercise_sessions` | astronaut | id, astronaut_id, exercise_type, duration, workload, repetitions |
| `bone_scans` | exams | id, astronaut_id, scan_type, scanned_at, report_reference |
| `bone_density_results` | exams | id, scan_id, bone_region, bmd_value, t_score, z_score |
| `functional_assessments` | exams | id, astronaut_id, test_type, protocol, score, assessed_at |
| `personal_dose_records` | environment | id, astronaut_id, dosimeter_id, dose_quantity, value, unit, interval |
| `radiation_area_records` | environment | id, location_id, sensor_id, radiation_metric, value, measured_at |
| `radiation_events` | environment | id, event_type, started_at, ended_at, status |
| `environmental_readings` | environment | id, location_id, metric_code, value, unit, measured_at |
| `environmental_samples` | environment | id, sample_type, location_id, sample_size, collected_at |
| `environmental_lab_results` | environment | id, sample_id, test_code, result_value, unit, verification |
| `mission_locations` | environment | id, mission_id, zone_name, location_type |
| `gravity_transition_events` | exams | id, mission_id, from_g, to_g, occurred_at |
| `sleep_sessions` | astronaut | id, astronaut_id, start_at, end_at, duration, source |
| `behavioral_checkins` | astronaut | id, astronaut_id, assessment_type, score, visibility_classification |
| `nutrition_logs` | astronaut | id, astronaut_id, meal_at, intake_details |
| `fluid_balance_logs` | astronaut | id, astronaut_id, period_start, period_end, intake, output, unit |
| `medication_administrations` | astronaut | id, astronaut_id, medication_reference, dose, unit, authorized_by |
| `health_alerts` | operations | id, rule_id, astronaut_id, location_id, severity, status |
| `alert_events` | operations | id, alert_id, event_type, actor_id, occurred_at |
| `alert_evidence` | operations | id, alert_id, source_record_type, source_record_id |
| `alert_rules` | operations | id, version, condition_definition, severity, approval_status |
| `medical_exam_schedule` | command | id, astronaut_id, exam_type, due_at, completion_status |
| `medical_procedures` | operations | id, title, version, approval_status, authoritative_source |
| `procedure_steps` | operations | id, procedure_id, step_order, instruction, acknowledgment_required |
| `medical_inventory` | operations | id, item_code, quantity, expiry_at, storage_location |
| `clinical_condition_catalog` | operations | id, condition_code, catalog_version, description |
| `recommendation_records` | operations | id, alert_id, procedure_id, displayed_at, action_status |
| `data_import_batches` | ground | id, source, imported_at, validation_summary |
| `sync_queue` | ground | id, event_id, destination, priority, status, attempt_count |
| `sync_receipts` | ground | id, event_id, acknowledged_at, remote_status |
| `audit_logs` | ground | id, actor_id, action, resource_type, resource_id, occurred_at |
| `data_quality_issues` | ground | id, record_reference, issue_type, severity, resolution_status |
| `attachments` | ground | id, owner_record_reference, storage_path, hash, access_classification |

All 57 tables are also searchable in Data & coverage. Domain fixtures directly display selected clinical records; identity, source, event and permission tables support those views through API projections. No synthetic rows are fabricated for absent official catalogs or files.

## Feature mapping

| ID | Requirement | Phase | Frontend assignment and current state |
|---|---|---|
| F01 | Mission and astronaut management | P0 | Command roster; mission/crew CRUD backend pending |
| F02 | User roles and clinical data permissions | P0 | Demo role filtering; Supabase sign-in/RLS pending |
| F03 | Device-agnostic sensor and report import | P0 | Source metadata shown; device/report upload adapters pending |
| F04 | Measurement validation and provenance | P0 | Symptom validation and vital/alert response validation; server validation pending |
| F05 | Personal health baseline management | P0 | Personal baseline display; baseline editor/version persistence pending |
| F06 | Shared symptom reporting | P0 | Working symptom form and proposed POST |
| F07 | Configurable, versioned clinical alert engine | P0 | Versioned demo fixtures and evidence UI; shared Python engine pending |
| F08 | Central medical incident handling | P0 | Incident-linked alarms and timeline; full incident lifecycle backend pending |
| F09 | Approved procedure and recommendation library | P0 | Demo procedure detail and acknowledgment; catalog API pending |
| F10 | Mission-aware examination scheduling | P0 | OCT due reminders, pre/post DXA; scheduling API pending |
| F11 | Local storage and offline operation | P0 | Browser-local fictional persistence; actual SQLite/grants/encryption pending |
| F12 | Ground synchronization and audit history | P0 | Demo queue/receipt presentation; authenticated idempotent sync pending |
| F13 | Cardiovascular vital signs and ECG reporting | P1 | Vitals, historical chart, ECG report review; waveform file absent |
| F14 | Respiratory and oxygenation monitoring | P0 | SpO2/RR, unavailable state and symptom escalation demo |
| F15 | Vascular ultrasound and D-dimer result review | P1 | Assay-aware D-dimer, side-specific Doppler review |
| F16 | Gravity-adaptation and vestibular assessments | P0 | Gravity transition and adaptation fixture |
| F17 | Cognitive and reaction-time assessments | P2 | Research reaction/balance metadata; P2 scoring source absent |
| F18 | Aerobic fitness and muscle assessments | P1 | Protocol-specific VO2peak and exercise context |
| F19 | Exercise and physical workload tracking | P0 | Exercise session and workout scenario; daily logging API pending |
| F20 | Bone-density and recovery examinations | P1 | Pre/post DXA records; no invented in-flight BMD |
| F21 | SANS/OCT, visual acuity and fundoscopy | P1 | Per-eye OCT due state and specialist review metadata |
| F22 | Sleep and circadian monitoring | P1 | Sleep duration and baseline fixture |
| F23 | Nutrition, hydration and fluid balance logs | P1 | Nutrition/fluid/authorized medication status metadata; log APIs pending |
| F24 | Behavioral-health check-ins | P1 | Private demo check-in form; production encrypted/private persistence pending |
| F25 | Personal and area radiation dosimetry | P0 | Separate dose quantities and stale source flag |
| F26 | Solar particle event and radiation incident monitoring | P0 | SPE demo event with shelter context |
| F27 | Cabin atmosphere and pressure monitoring | P0 | CO2/O2/pressure location and window metadata |
| F28 | Light and noise monitoring | P1 | Lux and dB(A) duration/weighting metadata |
| F29 | Environmental microbial sampling | P1 | Environmental specimen/method display |
| F30 | Water, air, food and surface test results | P0 | Water culture, other sample types pending records |
| F31 | Spacesuit microbial hygiene records where available | P2 | P2 spacesuit hygiene explicitly source-pending |
| F32 | Blood, saliva, urine and other sample management | P1 | Biological specimen/custody view; collection API pending |
| F33 | Onboard and Earth-laboratory test imports | P1 | Bio-Analyzer/ACTIS-like provenance; imports pending |
| F34 | Immune and viral biomarker result histories | P1 | Viral assay history review; no invented immune score |
| F35 | Sequencing and multi-omics dataset records where available | P2 | P2 sequencing metadata and review; files absent |
| F36 | Medical inventory and consumables | P1 | Demo inventory summary with expiry/location; item CRUD pending |
| F37 | Versioned condition-reference catalog | P1 | Catalog import boundary and demo count requirement; official source absent |
| F38 | Emergency clinical notification and acknowledgment | P0 | Visual/audio alert and acknowledgment; backend delivery pending |
| F39 | Offline crew guidance access | P0 | Demo guidance availability and expiry block; durable offline caches pending |
| F40 | Mission Medical Command dashboard | P0 | Mission command implemented |
| F41 | Individual Astronaut Health dashboard | P0 | Individual astronaut health implemented |
| F42 | Clinical Examinations and Recovery dashboard | P0 | Exams & recovery implemented |
| F43 | Radiation and Environment dashboard | P0 | Radiation & habitat implemented |
| F44 | Laboratory and Immune Health dashboard | P1 | Laboratory & immune implemented |
| F45 | Crew Self-Assessment dashboard | P0 | Crew self-assessment implemented |
| F46 | Ground Medical Review dashboard | P0 | Ground medical review implemented |
| F47 | Synthetic end-to-end mission demonstration | P0 | Twelve UI scenarios; full backend integration replay pending |

## Required full seed versus display fixtures

Backend seed requirement: seed=20261115; 180-day mission, 30 calendar days, four crew, three locations, five roles, 8–12 devices; 8,640 hourly HR/SpO2/RR + 240 BP rows; four ECG reports; eight per-eye ocular results as specified, eight vascular reports, eight fitness tests, eight DXA region results; 120 sleep and 120 exercise sessions; 24 symptoms; 20 check-ins; 120 personal dose intervals; 720 CO2, 240 O2/pressure, 12 SPE context readings; 24 biological samples, 32 lab results, 12 environmental samples, 16 environmental results, four sequencing runs; 20 DEMO catalog entries, 12 inventory items, eight demo procedures, eight incidents/alerts; 30 queued events, eight delayed receipts, five retry and four duplicate replay tests.

The frontend seed is intentionally a compact display dataset with 24 current vital measurements and associated 30-point trends, plus per-domain record cards. These quantities are not misrepresented as the full SQL seed. The backend team must implement the specified CLI and manifest.

## Every-source-data policy

The PDF contains no real astronaut identities, approved numeric clinical thresholds, medical imaging, full official catalogs or deployable backend. The frontend uses explicitly fictional crew and illustrative geometry; missing files/results stay unavailable. Backend acceptance tests must verify actual migrations, full-volume counts, event idempotency, durable SQLite and authorization.
