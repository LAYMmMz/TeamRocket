-- Curated, reproducible Supabase snapshot for the public Data Tables page.
-- Run by a trusted database operator. No private rows or table-wide clinical
-- counts are published; counts refer ONLY to fixed synthetic demonstration seeds.
-- This is a snapshot at inspected_at, not a real-time monitoring endpoint.
BEGIN;
WITH required AS (
 SELECT x.table_name,x.starter_fields
 FROM jsonb_to_recordset('[{"table_name":"astronauts","starter_fields":["id","crew_code","display_name","status"]},{"table_name":"missions","starter_fields":["id","name","mission_type","launch_at","landing_at","phase"]},{"table_name":"mission_crew","starter_fields":["mission_id","astronaut_id","crew_role"]},{"table_name":"users","starter_fields":["id","authentication_identity","account_status"]},{"table_name":"roles","starter_fields":["id","role_name","permissions"]},{"table_name":"user_role_assignments","starter_fields":["user_id","role_id","mission_id"]},{"table_name":"devices","starter_fields":["id","device_type","model","calibration_status"]},{"table_name":"device_assignments","starter_fields":["device_id","astronaut_id","location_id","assigned_at","ended_at"]},{"table_name":"vital_signs","starter_fields":["id","astronaut_id","metric_code","value","unit","measured_at","source_device_id","quality"]},{"table_name":"ecg_records","starter_fields":["id","astronaut_id","start_at","end_at","waveform_reference","reviewed_interpretation"]},{"table_name":"symptom_reports","starter_fields":["id","astronaut_id","symptom_code","severity","onset_at","reported_at","body_location"]},{"table_name":"health_baselines","starter_fields":["id","astronaut_id","metric_code","baseline_value","measurement_method","validity"]},{"table_name":"medical_findings","starter_fields":["id","astronaut_id","finding_code","interpretation","reviewer_id","reviewed_at"]},{"table_name":"medical_incidents","starter_fields":["id","astronaut_id","mission_id","incident_type","priority","status"]},{"table_name":"incident_events","starter_fields":["id","incident_id","event_type","actor_id","occurred_at"]},{"table_name":"biological_samples","starter_fields":["id","astronaut_id","sample_type","collected_at","source","processing_status"]},{"table_name":"laboratory_results","starter_fields":["id","sample_id","test_code","result_value","unit","assay_method","verification"]},{"table_name":"microbial_identifications","starter_fields":["id","sample_id","organism","identification_method","result_status"]},{"table_name":"sequencing_runs","starter_fields":["id","sample_id","platform","run_quality","data_reference"]},{"table_name":"clinical_sample_chain","starter_fields":["id","sample_id","custody_event","responsible_person","occurred_at"]},{"table_name":"vascular_ultrasound_results","starter_fields":["id","astronaut_id","vein","side","flow_pattern","thrombus_finding","reviewed_by"]},{"table_name":"ocular_assessments","starter_fields":["id","astronaut_id","test_type","assessed_at","report_reference"]},{"table_name":"ocular_results","starter_fields":["id","assessment_id","eye","metric_code","value","unit","interpretation"]},{"table_name":"fitness_assessments","starter_fields":["id","astronaut_id","test_type","metric_code","value","protocol","assessed_at"]},{"table_name":"exercise_sessions","starter_fields":["id","astronaut_id","exercise_type","duration","workload","repetitions"]},{"table_name":"bone_scans","starter_fields":["id","astronaut_id","scan_type","scanned_at","report_reference"]},{"table_name":"bone_density_results","starter_fields":["id","scan_id","bone_region","bmd_value","t_score","z_score"]},{"table_name":"functional_assessments","starter_fields":["id","astronaut_id","test_type","protocol","score","assessed_at"]},{"table_name":"personal_dose_records","starter_fields":["id","astronaut_id","dosimeter_id","dose_quantity","value","unit","interval"]},{"table_name":"radiation_area_records","starter_fields":["id","location_id","sensor_id","radiation_metric","value","measured_at"]},{"table_name":"radiation_events","starter_fields":["id","event_type","started_at","ended_at","status"]},{"table_name":"environmental_readings","starter_fields":["id","location_id","metric_code","value","unit","measured_at"]},{"table_name":"environmental_samples","starter_fields":["id","sample_type","location_id","sample_size","collected_at"]},{"table_name":"environmental_lab_results","starter_fields":["id","sample_id","test_code","result_value","unit","verification"]},{"table_name":"mission_locations","starter_fields":["id","mission_id","zone_name","location_type"]},{"table_name":"gravity_transition_events","starter_fields":["id","mission_id","from_g","to_g","occurred_at"]},{"table_name":"sleep_sessions","starter_fields":["id","astronaut_id","start_at","end_at","duration","source"]},{"table_name":"behavioral_checkins","starter_fields":["id","astronaut_id","assessment_type","score","visibility_classification"]},{"table_name":"nutrition_logs","starter_fields":["id","astronaut_id","meal_at","intake_details"]},{"table_name":"fluid_balance_logs","starter_fields":["id","astronaut_id","period_start","period_end","intake","output","unit"]},{"table_name":"medication_administrations","starter_fields":["id","astronaut_id","medication_reference","dose","unit","authorized_by"]},{"table_name":"health_alerts","starter_fields":["id","rule_id","astronaut_id","location_id","severity","status"]},{"table_name":"alert_events","starter_fields":["id","alert_id","event_type","actor_id","occurred_at"]},{"table_name":"alert_evidence","starter_fields":["id","alert_id","source_record_type","source_record_id"]},{"table_name":"alert_rules","starter_fields":["id","version","condition_definition","severity","approval_status"]},{"table_name":"medical_exam_schedule","starter_fields":["id","astronaut_id","exam_type","due_at","completion_status"]},{"table_name":"medical_procedures","starter_fields":["id","title","version","approval_status","authoritative_source"]},{"table_name":"procedure_steps","starter_fields":["id","procedure_id","step_order","instruction","acknowledgment_required"]},{"table_name":"medical_inventory","starter_fields":["id","item_code","quantity","expiry_at","storage_location"]},{"table_name":"clinical_condition_catalog","starter_fields":["id","condition_code","catalog_version","description"]},{"table_name":"recommendation_records","starter_fields":["id","alert_id","procedure_id","displayed_at","action_status"]},{"table_name":"data_import_batches","starter_fields":["id","source","imported_at","validation_summary"]},{"table_name":"sync_queue","starter_fields":["id","event_id","destination","priority","status","attempt_count"]},{"table_name":"sync_receipts","starter_fields":["id","event_id","acknowledged_at","remote_status"]},{"table_name":"audit_logs","starter_fields":["id","actor_id","action","resource_type","resource_id","occurred_at"]},{"table_name":"data_quality_issues","starter_fields":["id","record_reference","issue_type","severity","resolution_status"]},{"table_name":"attachments","starter_fields":["id","owner_record_reference","storage_path","hash","access_classification"]}]'::jsonb) AS x(table_name text,starter_fields text[])
), status AS (
 SELECT r.table_name,
    EXISTS (SELECT 1 FROM information_schema.tables t
      WHERE t.table_schema='public' AND t.table_name=r.table_name AND t.table_type='BASE TABLE') AS table_present,
    cardinality(r.starter_fields) AS starter_field_count,
    ARRAY(SELECT required_field
      FROM unnest(r.starter_fields) required_field
      WHERE NOT EXISTS (SELECT 1 FROM information_schema.columns c
        WHERE c.table_schema='public' AND c.table_name=r.table_name
          AND c.column_name=required_field)
      ORDER BY required_field) AS missing_starter_fields
 FROM required r
),published AS (
 SELECT s.*, (s.table_present AND cardinality(s.missing_starter_fields)=0) AS starter_fields_verified,
 CASE s.table_name
  WHEN 'missions' THEN (select count(*)::int from public.missions where id=md5('RP-DEMO-01-20261115')::uuid)
 WHEN 'mission_crew' THEN (select count(*)::int from public.mission_crew where mission_id=md5('RP-DEMO-01-20261115')::uuid)
 WHEN 'devices' THEN (select count(*)::int from public.devices where model like 'RP-DEMO-INSTRUMENT-%')
 WHEN 'mission_locations' THEN (select count(*)::int from public.mission_locations where mission_id='DEMO-01' and zone_name in ('HABITAT','MEDICAL_BAY','EXERCISE_AREA'))
 WHEN 'vital_signs' THEN (select count(*)::int from public.vital_signs where is_synthetic and event_id like 'RP-SEED-20261115-%')
 WHEN 'environmental_readings' THEN (select count(*)::int from public.environmental_readings where source_type='SIMULATED' and mission_id='DEMO-01')
 WHEN 'sleep_sessions' THEN (select count(*)::int from public.sleep_sessions where source_type='SIMULATED' and mission_id='DEMO-01')
 WHEN 'exercise_sessions' THEN (select count(*)::int from public.exercise_sessions where exercise_type='SIMULATED_TREADMILL')
 WHEN 'biological_samples' THEN (select count(*)::int from public.biological_samples where source='SIMULATED_ONBOARD_COLLECTION')
 WHEN 'laboratory_results' THEN (select count(*)::int from public.laboratory_results where test_code in ('DEMO_MARKER_A','DEMO_MARKER_B'))
 WHEN 'clinical_sample_chain' THEN (select count(*)::int from public.clinical_sample_chain where custody_event='SIMULATED_COLLECTED')
 WHEN 'ocular_assessments' THEN (select count(*)::int from public.ocular_assessments where test_type='SIMULATED_OCT')
 WHEN 'ocular_results' THEN (select count(*)::int from public.ocular_results where metric_code='DEMO_RNFL_THICKNESS')
 WHEN 'vascular_ultrasound_results' THEN (select count(*)::int from public.vascular_ultrasound_results where is_synthetic and measurement_method='DEMO_DOPPLER')
 WHEN 'bone_scans' THEN (select count(*)::int from public.bone_scans where scan_type='SIMULATED_GROUND_DXA')
 WHEN 'bone_density_results' THEN (select count(*)::int from public.bone_density_results where measurement_method='SIMULATED_GROUND_DXA')
 ELSE NULL::int
 END AS published_synthetic_rows
 FROM status s
)
INSERT INTO public.rocketpulse_public_schema_catalog
 (table_name,table_present,starter_fields_verified,starter_field_count,
 missing_starter_fields,published_synthetic_rows,inspected_at,approved_for_public,source_label)
SELECT table_name,table_present,starter_fields_verified,starter_field_count,
 missing_starter_fields,published_synthetic_rows,now(),true,'verified_supabase_metadata_snapshot'
FROM published
ON CONFLICT (table_name) DO UPDATE SET
 table_present=EXCLUDED.table_present,
 starter_fields_verified=EXCLUDED.starter_fields_verified,
 starter_field_count=EXCLUDED.starter_field_count,
 missing_starter_fields=EXCLUDED.missing_starter_fields,
 published_synthetic_rows=EXCLUDED.published_synthetic_rows,
 inspected_at=EXCLUDED.inspected_at,
 approved_for_public=EXCLUDED.approved_for_public;
COMMIT;
