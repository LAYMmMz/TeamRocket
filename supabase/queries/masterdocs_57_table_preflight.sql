-- Read-only MasterDocs preflight: 57 canonical logical tables and mandatory starter columns.
-- This cannot prove constraints, role-scoped RLS policies, deterministic seed or full scenario acceptance.
WITH expected(table_name, required_columns) AS (
 VALUES
  ('astronauts', ARRAY['id','crew_code','display_name','status' ]::text[]),
  ('missions', ARRAY['id','name','mission_type','launch_at','landing_at','phase' ]::text[]),
  ('mission_crew', ARRAY['mission_id','astronaut_id','crew_role' ]::text[]),
  ('users', ARRAY['id','authentication_identity','account_status' ]::text[]),
  ('roles', ARRAY['id','role_name','permissions' ]::text[]),
  ('user_role_assignments', ARRAY['user_id','role_id','mission_id' ]::text[]),
  ('devices', ARRAY['id','device_type','model','calibration_status' ]::text[]),
  ('device_assignments', ARRAY['device_id','astronaut_id','location_id','assigned_at','ended_at' ]::text[]),
  ('vital_signs', ARRAY['id','astronaut_id','metric_code','value','unit','measured_at','source_device_id','quality' ]::text[]),
  ('ecg_records', ARRAY['id','astronaut_id','start_at','end_at','waveform_reference','reviewed_interpretation' ]::text[]),
  ('symptom_reports', ARRAY['id','astronaut_id','symptom_code','severity','onset_at','reported_at','body_location' ]::text[]),
  ('health_baselines', ARRAY['id','astronaut_id','metric_code','baseline_value','measurement_method','validity' ]::text[]),
  ('medical_findings', ARRAY['id','astronaut_id','finding_code','interpretation','reviewer_id','reviewed_at' ]::text[]),
  ('medical_incidents', ARRAY['id','astronaut_id','mission_id','incident_type','priority','status' ]::text[]),
  ('incident_events', ARRAY['id','incident_id','event_type','actor_id','occurred_at' ]::text[]),
  ('biological_samples', ARRAY['id','astronaut_id','sample_type','collected_at','source','processing_status' ]::text[]),
  ('laboratory_results', ARRAY['id','sample_id','test_code','result_value','unit','assay_method','verification' ]::text[]),
  ('microbial_identifications', ARRAY['id','sample_id','organism','identification_method','result_status' ]::text[]),
  ('sequencing_runs', ARRAY['id','sample_id','platform','run_quality','data_reference' ]::text[]),
  ('clinical_sample_chain', ARRAY['id','sample_id','custody_event','responsible_person','occurred_at' ]::text[]),
  ('vascular_ultrasound_results', ARRAY['id','astronaut_id','vein','side','flow_pattern','thrombus_finding','reviewed_by' ]::text[]),
  ('ocular_assessments', ARRAY['id','astronaut_id','test_type','assessed_at','report_reference' ]::text[]),
  ('ocular_results', ARRAY['id','assessment_id','eye','metric_code','value','unit','interpretation' ]::text[]),
  ('fitness_assessments', ARRAY['id','astronaut_id','test_type','metric_code','value','protocol','assessed_at' ]::text[]),
  ('exercise_sessions', ARRAY['id','astronaut_id','exercise_type','duration','workload','repetitions' ]::text[]),
  ('bone_scans', ARRAY['id','astronaut_id','scan_type','scanned_at','report_reference' ]::text[]),
  ('bone_density_results', ARRAY['id','scan_id','bone_region','bmd_value','t_score','z_score' ]::text[]),
  ('functional_assessments', ARRAY['id','astronaut_id','test_type','protocol','score','assessed_at' ]::text[]),
  ('personal_dose_records', ARRAY['id','astronaut_id','dosimeter_id','dose_quantity','value','unit','interval' ]::text[]),
  ('radiation_area_records', ARRAY['id','location_id','sensor_id','radiation_metric','value','measured_at' ]::text[]),
  ('radiation_events', ARRAY['id','event_type','started_at','ended_at','status' ]::text[]),
  ('environmental_readings', ARRAY['id','location_id','metric_code','value','unit','measured_at' ]::text[]),
  ('environmental_samples', ARRAY['id','sample_type','location_id','sample_size','collected_at' ]::text[]),
  ('environmental_lab_results', ARRAY['id','sample_id','test_code','result_value','unit','verification' ]::text[]),
  ('mission_locations', ARRAY['id','mission_id','zone_name','location_type' ]::text[]),
  ('gravity_transition_events', ARRAY['id','mission_id','from_g','to_g','occurred_at' ]::text[]),
  ('sleep_sessions', ARRAY['id','astronaut_id','start_at','end_at','duration','source' ]::text[]),
  ('behavioral_checkins', ARRAY['id','astronaut_id','assessment_type','score','visibility_classification' ]::text[]),
  ('nutrition_logs', ARRAY['id','astronaut_id','meal_at','intake_details' ]::text[]),
  ('fluid_balance_logs', ARRAY['id','astronaut_id','period_start','period_end','intake','output','unit' ]::text[]),
  ('medication_administrations', ARRAY['id','astronaut_id','medication_reference','dose','unit','authorized_by' ]::text[]),
  ('health_alerts', ARRAY['id','rule_id','astronaut_id','location_id','severity','status' ]::text[]),
  ('alert_events', ARRAY['id','alert_id','event_type','actor_id','occurred_at' ]::text[]),
  ('alert_evidence', ARRAY['id','alert_id','source_record_type','source_record_id' ]::text[]),
  ('alert_rules', ARRAY['id','version','condition_definition','severity','approval_status' ]::text[]),
  ('medical_exam_schedule', ARRAY['id','astronaut_id','exam_type','due_at','completion_status' ]::text[]),
  ('medical_procedures', ARRAY['id','title','version','approval_status','authoritative_source' ]::text[]),
  ('procedure_steps', ARRAY['id','procedure_id','step_order','instruction','acknowledgment_required' ]::text[]),
  ('medical_inventory', ARRAY['id','item_code','quantity','expiry_at','storage_location' ]::text[]),
  ('clinical_condition_catalog', ARRAY['id','condition_code','catalog_version','description' ]::text[]),
  ('recommendation_records', ARRAY['id','alert_id','procedure_id','displayed_at','action_status' ]::text[]),
  ('data_import_batches', ARRAY['id','source','imported_at','validation_summary' ]::text[]),
  ('sync_queue', ARRAY['id','event_id','destination','priority','status','attempt_count' ]::text[]),
  ('sync_receipts', ARRAY['id','event_id','acknowledged_at','remote_status' ]::text[]),
  ('audit_logs', ARRAY['id','actor_id','action','resource_type','resource_id','occurred_at' ]::text[]),
  ('data_quality_issues', ARRAY['id','record_reference','issue_type','severity','resolution_status' ]::text[]),
  ('attachments', ARRAY['id','owner_record_reference','storage_path','hash','access_classification' ]::text[])
), columns_found AS (
 SELECT table_name, array_agg(column_name::text) AS columns
 FROM information_schema.columns WHERE table_schema='public' GROUP BY table_name
)
SELECT e.table_name, (tbl.table_name IS NOT NULL) AS exists_in_public,
 ARRAY(SELECT col FROM unnest(e.required_columns) AS col
       WHERE NOT col = ANY(coalesce(c.columns,ARRAY[]::text[])) ORDER BY col) AS missing_starter_columns,
 coalesce(pg.relrowsecurity,false) AS rls_enabled,
 CASE WHEN tbl.table_name IS NULL THEN 'MISSING TABLE'
      WHEN EXISTS(SELECT 1 FROM unnest(e.required_columns) col WHERE NOT col=ANY(coalesce(c.columns,ARRAY[]::text[]))) THEN 'MISSING COLUMNS'
      WHEN NOT coalesce(pg.relrowsecurity,false) THEN 'RLS DISABLED'
      ELSE 'STRUCTURE ONLY - OTHER GATES STILL PENDING' END AS preflight_status
FROM expected e
LEFT JOIN information_schema.tables tbl ON tbl.table_schema='public' AND tbl.table_name=e.table_name
LEFT JOIN columns_found c ON c.table_name=e.table_name
LEFT JOIN pg_class pg ON pg.relname=e.table_name AND pg.relnamespace='public'::regnamespace
ORDER BY e.table_name;
