-- MasterDocs clinical research demonstration fixtures. Deterministic and idempotent.
-- All readings refer to FICTIONAL crew and require clinician review;
-- do not infer diagnosis, treatment, NASA approval, or in-flight DXA.
BEGIN;
-- 120 sleep intervals and 120 exercise sessions.
INSERT INTO public.sleep_sessions
(id,astronaut_id,start_at,end_at,original_value,source_type,mission_id,
 measured_at,original_unit,quality_status,verification_status)
SELECT md5('RP-SLEEP-20261115-'||a.crew_code||'-'||d.n)::uuid,a.id,
 timestamptz '2026-10-17 22:00:00+00'+d.n*interval '1 day',
 timestamptz '2026-10-18 05:30:00+00'+d.n*interval '1 day',
 (450+(d.n%5)*6)::numeric,'SIMULATED','DEMO-01',
 timestamptz '2026-10-18 05:30:00+00'+d.n*interval '1 day','minutes',
 'VALID','UNVERIFIED'
FROM public.astronauts a CROSS JOIN generate_series(0,29) d(n)
WHERE a.crew_code IN ('CREW-01','CREW-02','CREW-03','CREW-04')
ON CONFLICT(id) DO NOTHING;
INSERT INTO public.exercise_sessions(id,astronaut_id,exercise_type,duration,workload,repetitions)
SELECT md5('RP-EXERCISE-20261115-'||a.crew_code||'-'||d.n)::uuid,a.id,
 'SIMULATED_TREADMILL',35+(d.n%6)*3,round((0.65+(d.n%5)*0.04)::numeric,2),0
FROM public.astronauts a CROSS JOIN generate_series(0,29) d(n)
WHERE a.crew_code IN ('CREW-01','CREW-02','CREW-03','CREW-04')
ON CONFLICT(id) DO NOTHING;
-- 24 biological samples, 32 assay-aware unreviewed lab results.
INSERT INTO public.biological_samples(id,astronaut_id,sample_type,collected_at,source,processing_status)
SELECT md5('RP-BIOSAMPLE-20261115-'||a.crew_code||'-'||s.n)::uuid,a.id,
 CASE WHEN s.n%3=0 THEN 'SIMULATED_BLOOD' WHEN s.n%3=1 THEN 'SIMULATED_SALIVA' ELSE 'SIMULATED_URINE' END,
 timestamptz '2026-10-20 09:00:00+00'+s.n*interval '1 day',
 'SIMULATED_ONBOARD_COLLECTION','ANALYZED'
FROM public.astronauts a CROSS JOIN generate_series(0,5) s(n)
WHERE a.crew_code IN ('CREW-01','CREW-02','CREW-03','CREW-04')
ON CONFLICT(id) DO NOTHING;
INSERT INTO public.laboratory_results(id,sample_id,test_code,result_value,unit,assay_method,verification)
SELECT md5('RP-LAB-20261115-'||a.crew_code||'-'||n.n)::uuid,
 md5('RP-BIOSAMPLE-20261115-'||a.crew_code||'-'||(n.n%6))::uuid,
 CASE WHEN n.n%2=0 THEN 'DEMO_MARKER_A' ELSE 'DEMO_MARKER_B' END,
 (1+(n.n%4)*0.1)::numeric,'arbitrary_unit','SIMULATED_NONCLINICAL_TEST','PENDING_CLINICIAN_REVIEW'
FROM public.astronauts a CROSS JOIN generate_series(0,7) n(n)
WHERE a.crew_code IN ('CREW-01','CREW-02','CREW-03','CREW-04')
ON CONFLICT(id) DO NOTHING;
INSERT INTO public.clinical_sample_chain(id,sample_id,custody_event,responsible_person,occurred_at)
SELECT md5('RP-CUSTODY-20261115-'||s.id::text)::uuid,s.id,'SIMULATED_COLLECTED',NULL,s.collected_at
FROM public.biological_samples s
WHERE s.source='SIMULATED_ONBOARD_COLLECTION'
ON CONFLICT(id) DO NOTHING;
-- 8 eye assessments (4 crew, each eye), region and eye kept distinct.
INSERT INTO public.ocular_assessments(id,astronaut_id,test_type,assessed_at,report_reference)
SELECT md5('RP-OCULAR-20261115-'||a.crew_code||'-'||e.eye)::uuid,
 a.id,'SIMULATED_OCT',
 timestamptz '2026-11-12 14:00:00+00',
 'DEMO-ONLY-'||a.crew_code||'-'||e.eye
FROM public.astronauts a CROSS JOIN (VALUES ('LEFT'),('RIGHT')) e(eye)
WHERE a.crew_code IN ('CREW-01','CREW-02','CREW-03','CREW-04')
ON CONFLICT(id) DO NOTHING;
INSERT INTO public.ocular_results(id,assessment_id,eye,metric_code,value,unit,interpretation,measurement_method)
SELECT md5('RP-OCULAR-RESULT-20261115-'||a.crew_code||'-'||e.eye)::uuid,
 md5('RP-OCULAR-20261115-'||a.crew_code||'-'||e.eye)::uuid,
 e.eye,'DEMO_RNFL_THICKNESS',100+right(a.crew_code,2)::int,'um',
 'SIMULATED_UNREVIEWED','DEMO_OCT_PROTOCOL'
FROM public.astronauts a CROSS JOIN (VALUES ('LEFT'),('RIGHT')) e(eye)
WHERE a.crew_code IN ('CREW-01','CREW-02','CREW-03','CREW-04')
ON CONFLICT(id) DO NOTHING;
-- Eight laterality-aware ultrasound records, no automated clot diagnosis.
INSERT INTO public.vascular_ultrasound_results
(id,astronaut_id,vein,side,flow_pattern,thrombus_finding,measurement_method,is_synthetic)
SELECT md5('RP-VASC-20261115-'||a.crew_code||'-'||e.side)::uuid,
 a.id,'INTERNAL_JUGULAR',e.side,'SIMULATED_NOT_REVIEWED','NONE_ASSERTED',
 'DEMO_DOPPLER',true
FROM public.astronauts a CROSS JOIN (VALUES ('LEFT'),('RIGHT')) e(side)
WHERE a.crew_code IN ('CREW-01','CREW-02','CREW-03','CREW-04')
ON CONFLICT(id) DO NOTHING;
-- 8 ground-only synthetic DXA scans and region-specific results.
INSERT INTO public.bone_scans(id,astronaut_id,scan_type,scanned_at,report_reference)
SELECT md5('RP-BONE-20261115-'||a.crew_code||'-'||z.phase)::uuid,
 a.id,'SIMULATED_GROUND_DXA',
 CASE WHEN z.phase='PREFLIGHT' THEN timestamptz '2026-05-20 10:00:00+00'
 ELSE timestamptz '2026-12-20 10:00:00+00' END,
 'DEMO-DXA-'||z.phase
FROM public.astronauts a CROSS JOIN (VALUES ('PREFLIGHT'),('POSTFLIGHT')) z(phase)
WHERE a.crew_code IN ('CREW-01','CREW-02','CREW-03','CREW-04')
ON CONFLICT(id) DO NOTHING;
INSERT INTO public.bone_density_results(id,scan_id,bone_region,bmd_value,t_score,z_score,measurement_method)
SELECT md5('RP-BMD-20261115-'||a.crew_code||'-'||z.phase)::uuid,
 md5('RP-BONE-20261115-'||a.crew_code||'-'||z.phase)::uuid,
 'LUMBAR_SPINE',1.01::numeric,NULL,NULL,'SIMULATED_GROUND_DXA'
FROM public.astronauts a CROSS JOIN (VALUES ('PREFLIGHT'),('POSTFLIGHT')) z(phase)
WHERE a.crew_code IN ('CREW-01','CREW-02','CREW-03','CREW-04')
ON CONFLICT(id) DO NOTHING;
COMMIT;
