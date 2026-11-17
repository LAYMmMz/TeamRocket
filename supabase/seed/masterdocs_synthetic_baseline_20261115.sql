-- TeamRocket deterministic TEST-ONLY seed (MasterDocs seed 20261115).
-- Safe on repeats; no DELETE/TRUNCATE or anonymous policy changes.
-- Real/clinical measurements are NEVER generated or implied.
-- Private canonical data is not exposed to the unauthenticated judge UI.
BEGIN;
INSERT INTO public.missions (id,name,mission_type,launch_at,landing_at,phase)
VALUES (md5('RP-DEMO-01-20261115')::uuid,'DEMO-01 · SIMULATED Deep-Space Mission','SIMULATED_RESEARCH','2026-06-01T00:00:00Z','2026-11-28T00:00:00Z','IN_FLIGHT')
ON CONFLICT (id) DO NOTHING;
INSERT INTO public.mission_crew (id,mission_id,astronaut_id,crew_role)
SELECT md5('RP-MEMBER-'||a.crew_code||'-20261115')::uuid,m.id,a.id,'SIMULATED_CREW'
FROM public.astronauts a
JOIN public.missions m ON m.id=md5('RP-DEMO-01-20261115')::uuid
WHERE a.crew_code IN ('CREW-01','CREW-02','CREW-03','CREW-04')
AND NOT EXISTS (SELECT 1 FROM public.mission_crew mc WHERE mc.mission_id=m.id AND mc.astronaut_id=a.id);
INSERT INTO public.mission_locations (id,mission_id,zone_name,location_type)
SELECT md5('RP-LOCATION-'||x.zone)::uuid,'DEMO-01',x.zone,x.kind
FROM (VALUES ('HABITAT','SIMULATED_HABITAT'),('MEDICAL_BAY','SIMULATED_MEDICAL'),('EXERCISE_AREA','SIMULATED_EXERCISE')) AS x(zone,kind)
ON CONFLICT (id) DO NOTHING;
INSERT INTO public.devices (id,device_type,model,calibration_status)
SELECT md5('RP-DEVICE-20261115-'||g.n)::uuid,
 CASE WHEN g.n<=4 THEN 'SYNTHETIC_VITAL_SENSOR' WHEN g.n<=6 THEN 'SYNTHETIC_DOSIMETER' ELSE 'SYNTHETIC_ENVIRONMENT' END,
 'RP-DEMO-INSTRUMENT-'||lpad(g.n::text,2,'0'),'SIMULATED_NOT_CERTIFIED'
FROM generate_series(1,8) g(n)
ON CONFLICT(id) DO NOTHING;
-- 4 fictional crew × 30 simulated days × 24 hourly observations × 3 metrics
-- plus BP twice daily × 4 crew × 30 days. No clinical interpretations.
WITH event_rows AS (
 SELECT a.id astronaut_id,a.crew_code,day.n d,h.n h,metric.code metric_code,metric.unit,
 CASE metric.code
 WHEN 'HR' THEN (68 + (right(a.crew_code,2)::int * 2) + ((day.n*3+h.n)%17))::numeric
 WHEN 'SpO2' THEN (96+((day.n+h.n)%3))::numeric
 WHEN 'RR' THEN (12+((day.n+h.n)%6))::numeric END AS value,
 timestamptz '2026-11-15 23:00:00+00' - (29-day.n)*interval '1 day' - (23-h.n)*interval '1 hour' AS measured_at
 FROM public.astronauts a CROSS JOIN generate_series(0,29) day(n)
 CROSS JOIN generate_series(0,23) h(n)
 CROSS JOIN (VALUES ('HR','bpm'),('SpO2','%'),('RR','breaths/min')) metric(code,unit)
 WHERE a.crew_code IN ('CREW-01','CREW-02','CREW-03','CREW-04')
), bp_rows AS (
 SELECT a.id astronaut_id,a.crew_code,day.n d,h.n h,'BP_SYS'::text metric_code,'mmHg'::text unit,
 (109+right(a.crew_code,2)::int*2 + ((day.n+h.n)%12))::numeric value,
 timestamptz '2026-11-15 00:00:00+00' - (29-day.n)*interval '1 day' + h.n*interval '12 hours' measured_at
 FROM public.astronauts a CROSS JOIN generate_series(0,29) day(n)
 CROSS JOIN generate_series(0,1) h(n)
 WHERE a.crew_code IN ('CREW-01','CREW-02','CREW-03','CREW-04')
), combined AS (SELECT * FROM event_rows UNION ALL SELECT * FROM bp_rows)
INSERT INTO public.vital_signs
(astronaut_id,metric_code,value,unit,measured_at,source_device_id,quality,mission_id,event_id,source_type,received_at,verification_status,is_synthetic)
SELECT astronaut_id,metric_code,value,unit,measured_at,
 md5('RP-DEVICE-20261115-'||right(crew_code,2)::int)::uuid,
 'VALID',md5('RP-DEMO-01-20261115')::uuid,
 'RP-SEED-20261115-VITAL-'||crew_code||'-'||metric_code||'-'||to_char(measured_at AT TIME ZONE 'UTC','YYYYMMDDHH24MI'),
 'SIMULATED',measured_at,'UNVERIFIED',true
FROM combined
ON CONFLICT (event_id) DO NOTHING;
-- 720 hourly synthetic CO2 readings for the habitat.
INSERT INTO public.environmental_readings
(id,location_id,metric_code,original_value,original_unit,measured_at,mission_id,
 source_type,quality_status,verification_status)
SELECT md5('RP-20261115-CO2-'||g.n)::uuid,md5('RP-LOCATION-HABITAT')::uuid,'CO2',
 (520 + (g.n%19)*11)::numeric,'ppm',
 timestamptz '2026-10-17 00:00:00+00' + g.n*interval '1 hour','DEMO-01',
 'SIMULATED','VALID','UNVERIFIED'
FROM generate_series(0,719) g(n)
ON CONFLICT(id) DO NOTHING;
COMMIT;
