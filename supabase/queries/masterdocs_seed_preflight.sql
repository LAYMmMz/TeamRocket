-- Read-only MasterDocs schema/seed acceptance preflight.
-- Run after both synthetic seed SQL files; never interpreted as medical validation.
WITH expected(table_name,expected_rows) AS (
 VALUES
 ('vital_signs',8880),('environmental_readings',720),
 ('sleep_sessions',120),('exercise_sessions',120),
 ('biological_samples',24),('laboratory_results',32),
 ('clinical_sample_chain',24),('ocular_assessments',8),
 ('ocular_results',8),('vascular_ultrasound_results',8),
 ('bone_scans',8),('bone_density_results',8)
),
counts AS (
 SELECT 'vital_signs' AS table_name,count(*)::bigint AS actual FROM public.vital_signs WHERE event_id LIKE 'RP-SEED-20261115-%'
 UNION ALL SELECT 'environmental_readings',count(*) FROM public.environmental_readings WHERE source_type='SIMULATED'
 UNION ALL SELECT 'sleep_sessions',count(*) FROM public.sleep_sessions WHERE source_type='SIMULATED'
 UNION ALL SELECT 'exercise_sessions',count(*) FROM public.exercise_sessions WHERE exercise_type='SIMULATED_TREADMILL'
 UNION ALL SELECT 'biological_samples',count(*) FROM public.biological_samples WHERE source='SIMULATED_ONBOARD_COLLECTION'
 UNION ALL SELECT 'laboratory_results',count(*) FROM public.laboratory_results WHERE test_code LIKE 'DEMO_MARKER_%'
 UNION ALL SELECT 'clinical_sample_chain',count(*) FROM public.clinical_sample_chain WHERE custody_event='SIMULATED_COLLECTED'
 UNION ALL SELECT 'ocular_assessments',count(*) FROM public.ocular_assessments WHERE test_type='SIMULATED_OCT'
 UNION ALL SELECT 'ocular_results',count(*) FROM public.ocular_results WHERE metric_code='DEMO_RNFL_THICKNESS'
 UNION ALL SELECT 'vascular_ultrasound_results',count(*) FROM public.vascular_ultrasound_results WHERE measurement_method='DEMO_DOPPLER'
 UNION ALL SELECT 'bone_scans',count(*) FROM public.bone_scans WHERE scan_type='SIMULATED_GROUND_DXA'
 UNION ALL SELECT 'bone_density_results',count(*) FROM public.bone_density_results WHERE measurement_method='SIMULATED_GROUND_DXA'
)
SELECT expected.table_name,expected.expected_rows,counts.actual,
 counts.actual=expected.expected_rows AS pass
FROM expected JOIN counts USING(table_name) ORDER BY expected.table_name;
-- Security review must also confirm individual RLS policies and restricted RPC EXECUTE,
-- not just relrowsecurity=true. This does not open medical tables to public viewers.
