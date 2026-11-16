# Full 47-feature frontend crosswalk

Source: uploaded *NASA Astronaut Health Monitoring — Final Development MasterDocs*, 15 November 2026, pp. 10–12.

**Status key:** Every feature is discoverable in the frontend at `/features/Fxx`. This is **not** a claim of integrated completion. Connected observation reads are available; complete feature acceptance still requires persistence, role checks and tests. See [current alignment and remaining blockers](../../docs/PDF_ALIGNMENT_STATUS.md).

| ID | Feature | Phase | Frontend path |
|---|---|---|---|
| F01 | Mission and astronaut management | P0 | `/features/F01` |
| F02 | User roles and clinical data permissions | P0 | `/features/F02` |
| F03 | Device-agnostic sensor and report import | P0 | `/features/F03` |
| F04 | Measurement validation and provenance | P0 | `/features/F04` |
| F05 | Personal health baseline management | P0 | `/features/F05` |
| F06 | Shared symptom reporting | P0 | `/features/F06` |
| F07 | Configurable, versioned clinical alert engine | P0 | `/features/F07` |
| F08 | Central medical incident handling | P0 | `/features/F08` |
| F09 | Approved procedure and recommendation library | P0 | `/features/F09` |
| F10 | Mission-aware examination scheduling | P0 | `/features/F10` |
| F11 | Local storage and offline operation | P0 | `/features/F11` |
| F12 | Ground synchronization and audit history | P0 | `/features/F12` |
| F13 | Cardiovascular vital signs and ECG reporting | P1 | `/features/F13` |
| F14 | Respiratory and oxygenation monitoring | P0 | `/features/F14` |
| F15 | Vascular ultrasound and D-dimer result review | P1 | `/features/F15` |
| F16 | Gravity-adaptation and vestibular assessments | P0 | `/features/F16` |
| F17 | Cognitive and reaction-time assessments | P2 | `/features/F17` |
| F18 | Aerobic fitness and muscle assessments | P1 | `/features/F18` |
| F19 | Exercise and physical workload tracking | P0 | `/features/F19` |
| F20 | Bone-density and recovery examinations | P1 | `/features/F20` |
| F21 | SANS/OCT, visual acuity and fundoscopy | P1 | `/features/F21` |
| F22 | Sleep and circadian monitoring | P1 | `/features/F22` |
| F23 | Nutrition, hydration and fluid balance logs | P1 | `/features/F23` |
| F24 | Behavioral-health check-ins | P1 | `/features/F24` |
| F25 | Personal and area radiation dosimetry | P0 | `/features/F25` |
| F26 | Solar particle event and radiation incident monitoring | P0 | `/features/F26` |
| F27 | Cabin atmosphere and pressure monitoring | P0 | `/features/F27` |
| F28 | Light and noise monitoring | P1 | `/features/F28` |
| F29 | Environmental microbial sampling | P1 | `/features/F29` |
| F30 | Water, air, food and surface test results | P0 | `/features/F30` |
| F31 | Spacesuit microbial hygiene records where available | P2 | `/features/F31` |
| F32 | Blood, saliva, urine and other sample management | P1 | `/features/F32` |
| F33 | Onboard and Earth-laboratory test imports | P1 | `/features/F33` |
| F34 | Immune and viral biomarker result histories | P1 | `/features/F34` |
| F35 | Sequencing and multi-omics dataset records where available | P2 | `/features/F35` |
| F36 | Medical inventory and consumables | P1 | `/features/F36` |
| F37 | Versioned condition-reference catalog | P1 | `/features/F37` |
| F38 | Emergency clinical notification and acknowledgment | P0 | `/features/F38` |
| F39 | Offline crew guidance access | P0 | `/features/F39` |
| F40 | Mission Medical Command dashboard | P0 | `/features/F40` |
| F41 | Individual Astronaut Health dashboard | P0 | `/features/F41` |
| F42 | Clinical Examinations and Recovery dashboard | P0 | `/features/F42` |
| F43 | Radiation and Environment dashboard | P0 | `/features/F43` |
| F44 | Laboratory and Immune Health dashboard | P1 | `/features/F44` |
| F45 | Crew Self-Assessment dashboard | P0 | `/features/F45` |
| F46 | Ground Medical Review dashboard | P0 | `/features/F46` |
| F47 | Synthetic end-to-end mission demonstration | P0 | `/features/F47` |

## Seven mandatory dashboards

| Dashboard | PDF ID | Frontend path | Minimum panels |
|---|---|---|---|
| Mission Medical Command | F40 | `/command` | Crew overview, mission phase, critical alerts, incidents, examination backlog and sync/device state |
| Individual Astronaut Health | F41 | `/individual` | Verified vitals and ECG, baseline, symptoms, exercise, sleep and history |
| Clinical Examinations & Recovery | F42 | `/examinations` | D-dimer/vascular, OCT/vision, DXA/bone, fitness, due examinations and review |
| Radiation & Environment | F43 | `/environment` | Personal dose and particle records, SPE, environment, lighting, noise and microbiology |
| Laboratory & Immune Health | F44 | `/laboratory` | Specimen custody, assay, instrument imports, sequencing and review |
| Crew Self-Assessment | F45 | `/crew` | Symptoms, fatigue, confidential check-ins, gravity adaptation, reminders and procedure acknowledgments |
| Ground Medical Review | F46 | `/ground` | Synced clinical review queue, delayed receipts, incident timelines, reviewer actions and audit |

## Twelve monitoring domains

| Domain | Feature IDs | Source tables | PDF safety behavior |
|---|---|---|---|
| Cardiovascular / Respiratory | F13, F14 | `vital_signs`, `ecg_records`, `health_baselines`, `symptom_reports` | Source quality and baseline; serious symptoms escalate manually even if SpO₂ missing |
| Vascular / Thrombosis | F15 | `laboratory_results`, `vascular_ultrasound_results`, `medical_findings` | Assay-aware findings; never automatically diagnose thrombosis |
| Radiation | F25, F26 | `personal_dose_records`, `radiation_area_records`, `radiation_events` | Dose-quantity compatibility, stale detector flag, no invented conversion |
| Gravity / Vestibular | F16, F17 | `gravity_transition_events`, `functional_assessments`, `symptom_reports`, `fluid_balance_logs` | Track adaptation cases; never autonomously clear EVA |
| Fitness / Muscle | F18, F19 | `fitness_assessments`, `exercise_sessions`, `functional_assessments` | Compare identical protocols and record adherence separately |
| Bone | F20 | `bone_scans`, `bone_density_results`, `exercise_sessions` | Pre/postflight comparisons only; never invent in-flight BMD |
| Vision / SANS | F21 | `ocular_assessments`, `ocular_results`, `medical_exam_schedule` | Eye-specific trend; specialist review and serious vision-symptom escalation |
| Immune / Infection | F32, F33, F34 | `biological_samples`, `laboratory_results`, `microbial_identifications`, `clinical_sample_chain` | Verify test methods and results; no inferred immune score |
| Sleep / Behavior | F22, F24 | `sleep_sessions`, `behavioral_checkins` | Trends versus baseline; restricted visibility |
| Cabin Environment | F27, F28 | `environmental_readings`, `mission_locations` | Location, unit and averaging-window-aware review |
| Environmental Microbiology | F29, F30, F31, F35 | `environmental_samples`, `environmental_lab_results`, `microbial_identifications`, `sequencing_runs` | Verification and follow-up sampling, no autonomous pathogen diagnosis |
| Autonomous Medical Operations | F08, F09, F36, F37, F38, F39 | `medical_incidents`, `incident_events`, `medical_procedures`, `procedure_steps`, `medical_inventory`, `clinical_condition_catalog` | Offline approved guidance, acknowledgement, clinician escalation and sync |

## 12 scenario demonstrations

| Scenario | Trigger | Expected output |
|---|---|---|
| S01 | Normal crew vitals and environment | Normal charts, simulation badges, no spurious clinical alerts |
| S02 | High HR coinciding with workout | Activity context; do not confuse elevated workout HR with resting abnormality |
| S03 | Serious breathing symptom; SpO₂ absent | Local incident; unavailable sensor remains missing, not fabricated |
| S04 | CO₂ time-window incident + headache symptom | One evidence-linked incident with a versioned demo rule and acknowledgement |
| S05 | Clinically unreviewed D-dimer | Review queue, never diagnose clot |
| S06 | Left-side vascular ultrasound finding | Left-side record and clinician review |
| S07 | Solar particle event + stale dosimeter | Labeled radiation notification, dose compatibility and stale flag |
| S08 | OCT due; no in-flight DXA | Reminders and missing BMD clearly marked; no invented readings |
| S09 | Environmental water culture flag | Show sampling method/unit, review and re-sampling request |
| S10 | Disconnect and reconnect | Local persistence, receipts, no duplicate alerts |
| S11 | Expired procedure and unapproved clinical rule | Historical reference only; no treatment guidance |
| S12 | Unauthorized confidential check-in access | Deny and audit in backend; UI demo shows restricted view |
