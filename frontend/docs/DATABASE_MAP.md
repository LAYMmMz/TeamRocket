# Canonical 57-Table PostgreSQL + Six-Table SQLite Inventory

Source: uploaded *Final MasterDocs*, pp. 3–6. Fields below are the **minimum starter field names in the PDF**, not implemented DDL. Create proper constraints in Supabase migrations.

| Group | Table | Minimum starter columns |
|---|---|---|
| Identity / missions / devices | `astronauts` | `id`, `crew_code`, `display_name`, `status` |
| Identity / missions / devices | `missions` | `id`, `name`, `mission_type`, `launch_at`, `landing_at`, `phase` |
| Identity / missions / devices | `mission_crew` | `mission_id`, `astronaut_id`, `crew_role` |
| Identity / missions / devices | `users` | `id`, `authentication_identity`, `account_status` |
| Identity / missions / devices | `roles` | `id`, `role_name`, `permissions` |
| Identity / missions / devices | `user_role_assignments` | `user_id`, `role_id`, `mission_id` |
| Identity / missions / devices | `devices` | `id`, `device_type`, `model`, `calibration_status` |
| Identity / missions / devices | `device_assignments` | `device_id`, `astronaut_id`, `location_id`, `assigned_at`, `ended_at` |
| General physiological health | `vital_signs` | `id`, `astronaut_id`, `metric_code`, `value`, `unit`, `measured_at`, `source_device_id`, `quality` |
| General physiological health | `ecg_records` | `id`, `astronaut_id`, `start_at`, `end_at`, `waveform_reference`, `reviewed_interpretation` |
| General physiological health | `symptom_reports` | `id`, `astronaut_id`, `symptom_code`, `severity`, `onset_at`, `reported_at`, `body_location` |
| General physiological health | `health_baselines` | `id`, `astronaut_id`, `metric_code`, `baseline_value`, `measurement_method`, `validity` |
| General physiological health | `medical_findings` | `id`, `astronaut_id`, `finding_code`, `interpretation`, `reviewer_id`, `reviewed_at` |
| General physiological health | `medical_incidents` | `id`, `astronaut_id`, `mission_id`, `incident_type`, `priority`, `status` |
| General physiological health | `incident_events` | `id`, `incident_id`, `event_type`, `actor_id`, `occurred_at` |
| Laboratory / immune | `biological_samples` | `id`, `astronaut_id`, `sample_type`, `collected_at`, `source`, `processing_status` |
| Laboratory / immune | `laboratory_results` | `id`, `sample_id`, `test_code`, `result_value`, `unit`, `assay_method`, `verification` |
| Laboratory / immune | `microbial_identifications` | `id`, `sample_id`, `organism`, `identification_method`, `result_status` |
| Laboratory / immune | `sequencing_runs` | `id`, `sample_id`, `platform`, `run_quality`, `data_reference` |
| Laboratory / immune | `clinical_sample_chain` | `id`, `sample_id`, `custody_event`, `responsible_person`, `occurred_at` |
| Cardiovascular / eye / fitness / bone | `vascular_ultrasound_results` | `id`, `astronaut_id`, `vein`, `side`, `flow_pattern`, `thrombus_finding`, `reviewed_by` |
| Cardiovascular / eye / fitness / bone | `ocular_assessments` | `id`, `astronaut_id`, `test_type`, `assessed_at`, `report_reference` |
| Cardiovascular / eye / fitness / bone | `ocular_results` | `id`, `assessment_id`, `eye`, `metric_code`, `value`, `unit`, `interpretation` |
| Cardiovascular / eye / fitness / bone | `fitness_assessments` | `id`, `astronaut_id`, `test_type`, `metric_code`, `value`, `protocol`, `assessed_at` |
| Cardiovascular / eye / fitness / bone | `exercise_sessions` | `id`, `astronaut_id`, `exercise_type`, `duration`, `workload`, `repetitions` |
| Cardiovascular / eye / fitness / bone | `bone_scans` | `id`, `astronaut_id`, `scan_type`, `scanned_at`, `report_reference` |
| Cardiovascular / eye / fitness / bone | `bone_density_results` | `id`, `scan_id`, `bone_region`, `bmd_value`, `t_score`, `z_score` |
| Cardiovascular / eye / fitness / bone | `functional_assessments` | `id`, `astronaut_id`, `test_type`, `protocol`, `score`, `assessed_at` |
| Radiation / environment / gravity | `personal_dose_records` | `id`, `astronaut_id`, `dosimeter_id`, `dose_quantity`, `value`, `unit`, `interval` |
| Radiation / environment / gravity | `radiation_area_records` | `id`, `location_id`, `sensor_id`, `radiation_metric`, `value`, `measured_at` |
| Radiation / environment / gravity | `radiation_events` | `id`, `event_type`, `started_at`, `ended_at`, `status` |
| Radiation / environment / gravity | `environmental_readings` | `id`, `location_id`, `metric_code`, `value`, `unit`, `measured_at` |
| Radiation / environment / gravity | `environmental_samples` | `id`, `sample_type`, `location_id`, `sample_size`, `collected_at` |
| Radiation / environment / gravity | `environmental_lab_results` | `id`, `sample_id`, `test_code`, `result_value`, `unit`, `verification` |
| Radiation / environment / gravity | `mission_locations` | `id`, `mission_id`, `zone_name`, `location_type` |
| Radiation / environment / gravity | `gravity_transition_events` | `id`, `mission_id`, `from_g`, `to_g`, `occurred_at` |
| Sleep / nutrition / fluids / medication | `sleep_sessions` | `id`, `astronaut_id`, `start_at`, `end_at`, `duration`, `source` |
| Sleep / nutrition / fluids / medication | `behavioral_checkins` | `id`, `astronaut_id`, `assessment_type`, `score`, `visibility_classification` |
| Sleep / nutrition / fluids / medication | `nutrition_logs` | `id`, `astronaut_id`, `meal_at`, `intake_details` |
| Sleep / nutrition / fluids / medication | `fluid_balance_logs` | `id`, `astronaut_id`, `period_start`, `period_end`, `intake`, `output`, `unit` |
| Sleep / nutrition / fluids / medication | `medication_administrations` | `id`, `astronaut_id`, `medication_reference`, `dose`, `unit`, `authorized_by` |
| Rules / alerts / procedures / exams | `health_alerts` | `id`, `rule_id`, `astronaut_id`, `location_id`, `severity`, `status` |
| Rules / alerts / procedures / exams | `alert_events` | `id`, `alert_id`, `event_type`, `actor_id`, `occurred_at` |
| Rules / alerts / procedures / exams | `alert_evidence` | `id`, `alert_id`, `source_record_type`, `source_record_id` |
| Rules / alerts / procedures / exams | `alert_rules` | `id`, `version`, `condition_definition`, `severity`, `approval_status` |
| Rules / alerts / procedures / exams | `medical_exam_schedule` | `id`, `astronaut_id`, `exam_type`, `due_at`, `completion_status` |
| Rules / alerts / procedures / exams | `medical_procedures` | `id`, `title`, `version`, `approval_status`, `authoritative_source` |
| Rules / alerts / procedures / exams | `procedure_steps` | `id`, `procedure_id`, `step_order`, `instruction`, `acknowledgment_required` |
| Rules / alerts / procedures / exams | `medical_inventory` | `id`, `item_code`, `quantity`, `expiry_at`, `storage_location` |
| Rules / alerts / procedures / exams | `clinical_condition_catalog` | `id`, `condition_code`, `catalog_version`, `description` |
| Rules / alerts / procedures / exams | `recommendation_records` | `id`, `alert_id`, `procedure_id`, `displayed_at`, `action_status` |
| Import / sync / audit | `data_import_batches` | `id`, `source`, `imported_at`, `validation_summary` |
| Import / sync / audit | `sync_queue` | `id`, `event_id`, `destination`, `priority`, `status`, `attempt_count` |
| Import / sync / audit | `sync_receipts` | `id`, `event_id`, `acknowledged_at`, `remote_status` |
| Import / sync / audit | `audit_logs` | `id`, `actor_id`, `action`, `resource_type`, `resource_id`, `occurred_at` |
| Import / sync / audit | `data_quality_issues` | `id`, `record_reference`, `issue_type`, `severity`, `resolution_status` |
| Import / sync / audit | `attachments` | `id`, `owner_record_reference`, `storage_path`, `hash`, `access_classification` |

## Six required onboard SQLite tables

| Local table | Cloud mapping | Minimum local fields |
|---|---|---|
| `offline_vital_signs` | vital_signs | `local_id`, `event_id`, `astronaut_id`, `mission_id`, `metric_code`, `value`, `unit`, `measured_at`, `received_at`, `quality`, `source_device_id`, `sync_status` |
| `offline_symptom_reports` | symptom_reports | `local_id`, `event_id`, `astronaut_id`, `mission_id`, `symptom_code`, `severity`, `onset_at`, `reported_at`, `notes`, `sync_status` |
| `offline_health_alerts` | health_alerts + evidence/events | `local_id`, `event_id`, `rule_id`, `rule_version`, `astronaut_id`, `location_id`, `severity`, `evidence`, `status`, `created_at`, `sync_status` |
| `offline_alert_rules` | alert_rules | `rule_id`, `version`, `definition`, `scope`, `approval_signature`, `valid_from`, `expires_at`, `stored_at` |
| `offline_medical_procedures` | medical_procedures + steps | `procedure_id`, `version`, `title`, `ordered_steps`, `source`, `approval_state`, `cached_at`, `validity` |
| `sync_queue` | sync receipts/events | `queue_id`, `event_id`, `entity_type`, `local_ref`, `operation`, `payload_hash`, `priority`, `attempts`, `next_retry_at`, `status`, `receipt_id` |

**Implementation invariants:** UUID primary keys (composite joins as appropriate), timestamptz UTC, numeric and units, FKs, quality, provenance, is_synthetic, immutable event_id, source and received timestamps, indices, RLS, audit, no cascading clinical history deletion. Local SQLite commits before remote synchronization; encryption is mandatory for deployed onboard data.
