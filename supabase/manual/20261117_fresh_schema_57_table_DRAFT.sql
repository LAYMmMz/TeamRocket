-- REVIEW-ONLY DRAFT — DO NOT APPLY TO TEAMROCKET PRODUCTION WITHOUT APPROVAL.
-- Intended for *fresh test project* planning; existing TeamRocketV2Database
-- may already have incompatible key types, tables and policies.
-- This file is not a successfully applied Supabase migration.
-- Source: MasterDocs 15 Nov 2026 pp. 3–5: EXACTLY 57 logical tables.
-- RLS is enabled by default, with no public clinical read/write policies.
-- No unsourced clinical thresholds, diagnoses or procedure approvals.
BEGIN;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Identity / missions / devices
CREATE TABLE IF NOT EXISTS public."astronauts" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "crew_code" text,
    "display_name" text,
    "status" text,
    CONSTRAINT "astronauts_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."astronauts" ENABLE ROW LEVEL SECURITY;

-- Identity / missions / devices
CREATE TABLE IF NOT EXISTS public."missions" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "name" text,
    "mission_type" text,
    "launch_at" timestamptz,
    "landing_at" timestamptz,
    "phase" text,
    CONSTRAINT "missions_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."missions" ENABLE ROW LEVEL SECURITY;

-- Identity / missions / devices
CREATE TABLE IF NOT EXISTS public."mission_crew" (
    "mission_id" uuid,
    "astronaut_id" uuid,
    "crew_role" text,
    CONSTRAINT "mission_crew_pkey" PRIMARY KEY ("mission_id","astronaut_id")
);
ALTER TABLE public."mission_crew" ENABLE ROW LEVEL SECURITY;

-- Identity / missions / devices
CREATE TABLE IF NOT EXISTS public."users" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "authentication_identity" text,
    "account_status" text,
    CONSTRAINT "users_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."users" ENABLE ROW LEVEL SECURITY;

-- Identity / missions / devices
CREATE TABLE IF NOT EXISTS public."roles" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "role_name" text,
    "permissions" jsonb,
    CONSTRAINT "roles_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."roles" ENABLE ROW LEVEL SECURITY;

-- Identity / missions / devices
CREATE TABLE IF NOT EXISTS public."user_role_assignments" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "user_id" uuid NOT NULL,
    "role_id" uuid NOT NULL,
    "mission_id" uuid,
    CONSTRAINT "user_role_assignments_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."user_role_assignments" ENABLE ROW LEVEL SECURITY;

-- Identity / missions / devices
CREATE TABLE IF NOT EXISTS public."devices" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "device_type" text,
    "model" text,
    "calibration_status" text,
    CONSTRAINT "devices_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."devices" ENABLE ROW LEVEL SECURITY;

-- Identity / missions / devices
CREATE TABLE IF NOT EXISTS public."device_assignments" (
    "device_id" uuid,
    "astronaut_id" uuid,
    "location_id" uuid,
    "assigned_at" timestamptz,
    "ended_at" timestamptz
);
ALTER TABLE public."device_assignments" ENABLE ROW LEVEL SECURITY;

-- General physiological health
CREATE TABLE IF NOT EXISTS public."vital_signs" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "astronaut_id" uuid,
    "metric_code" text,
    "value" numeric,
    "unit" text,
    "measured_at" timestamptz,
    "source_device_id" text,
    "quality" text,
    "is_synthetic" boolean NOT NULL DEFAULT false,
    "source_type" text,
    "received_at" timestamptz,
    "verification" text,
    "event_id" text,
    CONSTRAINT "vital_signs_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."vital_signs" ENABLE ROW LEVEL SECURITY;
CREATE UNIQUE INDEX IF NOT EXISTS "vital_signs_event_id_unique" ON public."vital_signs" ("event_id") WHERE "event_id" IS NOT NULL;
CREATE INDEX IF NOT EXISTS "vital_signs_crew_measured_idx" ON public."vital_signs" ("astronaut_id","measured_at" DESC);

-- General physiological health
CREATE TABLE IF NOT EXISTS public."ecg_records" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "astronaut_id" uuid,
    "start_at" timestamptz,
    "end_at" timestamptz,
    "waveform_reference" text,
    "reviewed_interpretation" text,
    "is_synthetic" boolean NOT NULL DEFAULT false,
    "source_type" text,
    "received_at" timestamptz,
    "quality" text,
    "verification" text,
    "event_id" text,
    CONSTRAINT "ecg_records_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."ecg_records" ENABLE ROW LEVEL SECURITY;
CREATE UNIQUE INDEX IF NOT EXISTS "ecg_records_event_id_unique" ON public."ecg_records" ("event_id") WHERE "event_id" IS NOT NULL;

-- General physiological health
CREATE TABLE IF NOT EXISTS public."symptom_reports" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "astronaut_id" uuid,
    "symptom_code" text,
    "severity" text,
    "onset_at" timestamptz,
    "reported_at" timestamptz,
    "body_location" text,
    "is_synthetic" boolean NOT NULL DEFAULT false,
    "source_type" text,
    "received_at" timestamptz,
    "quality" text,
    "verification" text,
    "event_id" text,
    CONSTRAINT "symptom_reports_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."symptom_reports" ENABLE ROW LEVEL SECURITY;
CREATE UNIQUE INDEX IF NOT EXISTS "symptom_reports_event_id_unique" ON public."symptom_reports" ("event_id") WHERE "event_id" IS NOT NULL;

-- General physiological health
CREATE TABLE IF NOT EXISTS public."health_baselines" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "astronaut_id" uuid,
    "metric_code" text,
    "baseline_value" numeric,
    "measurement_method" text,
    "validity" text,
    "is_synthetic" boolean NOT NULL DEFAULT false,
    "source_type" text,
    "received_at" timestamptz,
    "quality" text,
    "verification" text,
    "event_id" text,
    CONSTRAINT "health_baselines_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."health_baselines" ENABLE ROW LEVEL SECURITY;
CREATE UNIQUE INDEX IF NOT EXISTS "health_baselines_event_id_unique" ON public."health_baselines" ("event_id") WHERE "event_id" IS NOT NULL;

-- General physiological health
CREATE TABLE IF NOT EXISTS public."medical_findings" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "astronaut_id" uuid,
    "finding_code" text,
    "interpretation" text,
    "reviewer_id" text,
    "reviewed_at" timestamptz,
    "is_synthetic" boolean NOT NULL DEFAULT false,
    "source_type" text,
    "received_at" timestamptz,
    "quality" text,
    "verification" text,
    "event_id" text,
    CONSTRAINT "medical_findings_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."medical_findings" ENABLE ROW LEVEL SECURITY;
CREATE UNIQUE INDEX IF NOT EXISTS "medical_findings_event_id_unique" ON public."medical_findings" ("event_id") WHERE "event_id" IS NOT NULL;

-- General physiological health
CREATE TABLE IF NOT EXISTS public."medical_incidents" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "astronaut_id" uuid,
    "mission_id" uuid,
    "incident_type" text,
    "priority" text,
    "status" text,
    "is_synthetic" boolean NOT NULL DEFAULT false,
    "source_type" text,
    "received_at" timestamptz,
    "quality" text,
    "verification" text,
    "event_id" text,
    CONSTRAINT "medical_incidents_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."medical_incidents" ENABLE ROW LEVEL SECURITY;
CREATE UNIQUE INDEX IF NOT EXISTS "medical_incidents_event_id_unique" ON public."medical_incidents" ("event_id") WHERE "event_id" IS NOT NULL;

-- General physiological health
CREATE TABLE IF NOT EXISTS public."incident_events" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "incident_id" uuid,
    "event_type" text,
    "actor_id" text,
    "occurred_at" timestamptz,
    CONSTRAINT "incident_events_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."incident_events" ENABLE ROW LEVEL SECURITY;

-- Laboratory / immune
CREATE TABLE IF NOT EXISTS public."biological_samples" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "astronaut_id" uuid,
    "sample_type" text,
    "collected_at" timestamptz,
    "source" text,
    "processing_status" text,
    "is_synthetic" boolean NOT NULL DEFAULT false,
    "source_type" text,
    "received_at" timestamptz,
    "quality" text,
    "verification" text,
    "event_id" text,
    CONSTRAINT "biological_samples_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."biological_samples" ENABLE ROW LEVEL SECURITY;
CREATE UNIQUE INDEX IF NOT EXISTS "biological_samples_event_id_unique" ON public."biological_samples" ("event_id") WHERE "event_id" IS NOT NULL;

-- Laboratory / immune
CREATE TABLE IF NOT EXISTS public."laboratory_results" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "sample_id" uuid,
    "test_code" text,
    "result_value" numeric,
    "unit" text,
    "assay_method" text,
    "verification" text,
    "is_synthetic" boolean NOT NULL DEFAULT false,
    "source_type" text,
    "received_at" timestamptz,
    "quality" text,
    "event_id" text,
    CONSTRAINT "laboratory_results_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."laboratory_results" ENABLE ROW LEVEL SECURITY;
CREATE UNIQUE INDEX IF NOT EXISTS "laboratory_results_event_id_unique" ON public."laboratory_results" ("event_id") WHERE "event_id" IS NOT NULL;

-- Laboratory / immune
CREATE TABLE IF NOT EXISTS public."microbial_identifications" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "sample_id" uuid,
    "organism" text,
    "identification_method" text,
    "result_status" text,
    "is_synthetic" boolean NOT NULL DEFAULT false,
    "source_type" text,
    "received_at" timestamptz,
    "quality" text,
    "verification" text,
    "event_id" text,
    CONSTRAINT "microbial_identifications_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."microbial_identifications" ENABLE ROW LEVEL SECURITY;
CREATE UNIQUE INDEX IF NOT EXISTS "microbial_identifications_event_id_unique" ON public."microbial_identifications" ("event_id") WHERE "event_id" IS NOT NULL;

-- Laboratory / immune
CREATE TABLE IF NOT EXISTS public."sequencing_runs" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "sample_id" uuid,
    "platform" text,
    "run_quality" text,
    "data_reference" text,
    "is_synthetic" boolean NOT NULL DEFAULT false,
    "source_type" text,
    "received_at" timestamptz,
    "quality" text,
    "verification" text,
    "event_id" text,
    CONSTRAINT "sequencing_runs_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."sequencing_runs" ENABLE ROW LEVEL SECURITY;
CREATE UNIQUE INDEX IF NOT EXISTS "sequencing_runs_event_id_unique" ON public."sequencing_runs" ("event_id") WHERE "event_id" IS NOT NULL;

-- Laboratory / immune
CREATE TABLE IF NOT EXISTS public."clinical_sample_chain" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "sample_id" uuid,
    "custody_event" text,
    "responsible_person" text,
    "occurred_at" timestamptz,
    CONSTRAINT "clinical_sample_chain_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."clinical_sample_chain" ENABLE ROW LEVEL SECURITY;

-- Cardiovascular / eye / fitness / bone
CREATE TABLE IF NOT EXISTS public."vascular_ultrasound_results" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "astronaut_id" uuid,
    "vein" text,
    "side" text,
    "flow_pattern" text,
    "thrombus_finding" text,
    "reviewed_by" text,
    "is_synthetic" boolean NOT NULL DEFAULT false,
    "source_type" text,
    "received_at" timestamptz,
    "quality" text,
    "verification" text,
    "event_id" text,
    CONSTRAINT "vascular_ultrasound_results_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."vascular_ultrasound_results" ENABLE ROW LEVEL SECURITY;
CREATE UNIQUE INDEX IF NOT EXISTS "vascular_ultrasound_results_event_id_unique" ON public."vascular_ultrasound_results" ("event_id") WHERE "event_id" IS NOT NULL;

-- Cardiovascular / eye / fitness / bone
CREATE TABLE IF NOT EXISTS public."ocular_assessments" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "astronaut_id" uuid,
    "test_type" text,
    "assessed_at" timestamptz,
    "report_reference" text,
    "is_synthetic" boolean NOT NULL DEFAULT false,
    "source_type" text,
    "received_at" timestamptz,
    "quality" text,
    "verification" text,
    "event_id" text,
    CONSTRAINT "ocular_assessments_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."ocular_assessments" ENABLE ROW LEVEL SECURITY;
CREATE UNIQUE INDEX IF NOT EXISTS "ocular_assessments_event_id_unique" ON public."ocular_assessments" ("event_id") WHERE "event_id" IS NOT NULL;

-- Cardiovascular / eye / fitness / bone
CREATE TABLE IF NOT EXISTS public."ocular_results" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "assessment_id" uuid,
    "eye" text,
    "metric_code" text,
    "value" numeric,
    "unit" text,
    "interpretation" text,
    CONSTRAINT "ocular_results_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."ocular_results" ENABLE ROW LEVEL SECURITY;

-- Cardiovascular / eye / fitness / bone
CREATE TABLE IF NOT EXISTS public."fitness_assessments" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "astronaut_id" uuid,
    "test_type" text,
    "metric_code" text,
    "value" numeric,
    "protocol" text,
    "assessed_at" timestamptz,
    "is_synthetic" boolean NOT NULL DEFAULT false,
    "source_type" text,
    "received_at" timestamptz,
    "quality" text,
    "verification" text,
    "event_id" text,
    CONSTRAINT "fitness_assessments_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."fitness_assessments" ENABLE ROW LEVEL SECURITY;
CREATE UNIQUE INDEX IF NOT EXISTS "fitness_assessments_event_id_unique" ON public."fitness_assessments" ("event_id") WHERE "event_id" IS NOT NULL;

-- Cardiovascular / eye / fitness / bone
CREATE TABLE IF NOT EXISTS public."exercise_sessions" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "astronaut_id" uuid,
    "exercise_type" text,
    "duration" numeric,
    "workload" numeric,
    "repetitions" numeric,
    "is_synthetic" boolean NOT NULL DEFAULT false,
    "source_type" text,
    "received_at" timestamptz,
    "quality" text,
    "verification" text,
    "event_id" text,
    CONSTRAINT "exercise_sessions_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."exercise_sessions" ENABLE ROW LEVEL SECURITY;
CREATE UNIQUE INDEX IF NOT EXISTS "exercise_sessions_event_id_unique" ON public."exercise_sessions" ("event_id") WHERE "event_id" IS NOT NULL;

-- Cardiovascular / eye / fitness / bone
CREATE TABLE IF NOT EXISTS public."bone_scans" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "astronaut_id" uuid,
    "scan_type" text,
    "scanned_at" timestamptz,
    "report_reference" text,
    "is_synthetic" boolean NOT NULL DEFAULT false,
    "source_type" text,
    "received_at" timestamptz,
    "quality" text,
    "verification" text,
    "event_id" text,
    CONSTRAINT "bone_scans_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."bone_scans" ENABLE ROW LEVEL SECURITY;
CREATE UNIQUE INDEX IF NOT EXISTS "bone_scans_event_id_unique" ON public."bone_scans" ("event_id") WHERE "event_id" IS NOT NULL;

-- Cardiovascular / eye / fitness / bone
CREATE TABLE IF NOT EXISTS public."bone_density_results" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "scan_id" uuid,
    "bone_region" text,
    "bmd_value" numeric,
    "t_score" numeric,
    "z_score" numeric,
    CONSTRAINT "bone_density_results_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."bone_density_results" ENABLE ROW LEVEL SECURITY;

-- Cardiovascular / eye / fitness / bone
CREATE TABLE IF NOT EXISTS public."functional_assessments" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "astronaut_id" uuid,
    "test_type" text,
    "protocol" text,
    "score" numeric,
    "assessed_at" timestamptz,
    "is_synthetic" boolean NOT NULL DEFAULT false,
    "source_type" text,
    "received_at" timestamptz,
    "quality" text,
    "verification" text,
    "event_id" text,
    CONSTRAINT "functional_assessments_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."functional_assessments" ENABLE ROW LEVEL SECURITY;
CREATE UNIQUE INDEX IF NOT EXISTS "functional_assessments_event_id_unique" ON public."functional_assessments" ("event_id") WHERE "event_id" IS NOT NULL;

-- Radiation / environment / gravity
CREATE TABLE IF NOT EXISTS public."personal_dose_records" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "astronaut_id" uuid,
    "dosimeter_id" text,
    "dose_quantity" text,
    "value" numeric,
    "unit" text,
    "interval" text,
    "is_synthetic" boolean NOT NULL DEFAULT false,
    "source_type" text,
    "received_at" timestamptz,
    "quality" text,
    "verification" text,
    "event_id" text,
    CONSTRAINT "personal_dose_records_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."personal_dose_records" ENABLE ROW LEVEL SECURITY;
CREATE UNIQUE INDEX IF NOT EXISTS "personal_dose_records_event_id_unique" ON public."personal_dose_records" ("event_id") WHERE "event_id" IS NOT NULL;

-- Radiation / environment / gravity
CREATE TABLE IF NOT EXISTS public."radiation_area_records" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "location_id" uuid,
    "sensor_id" text,
    "radiation_metric" text,
    "value" numeric,
    "measured_at" timestamptz,
    "is_synthetic" boolean NOT NULL DEFAULT false,
    "source_type" text,
    "received_at" timestamptz,
    "quality" text,
    "verification" text,
    "event_id" text,
    CONSTRAINT "radiation_area_records_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."radiation_area_records" ENABLE ROW LEVEL SECURITY;
CREATE UNIQUE INDEX IF NOT EXISTS "radiation_area_records_event_id_unique" ON public."radiation_area_records" ("event_id") WHERE "event_id" IS NOT NULL;

-- Radiation / environment / gravity
CREATE TABLE IF NOT EXISTS public."radiation_events" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "event_type" text,
    "started_at" timestamptz,
    "ended_at" timestamptz,
    "status" text,
    "is_synthetic" boolean NOT NULL DEFAULT false,
    "source_type" text,
    "received_at" timestamptz,
    "quality" text,
    "verification" text,
    "event_id" text,
    CONSTRAINT "radiation_events_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."radiation_events" ENABLE ROW LEVEL SECURITY;
CREATE UNIQUE INDEX IF NOT EXISTS "radiation_events_event_id_unique" ON public."radiation_events" ("event_id") WHERE "event_id" IS NOT NULL;

-- Radiation / environment / gravity
CREATE TABLE IF NOT EXISTS public."environmental_readings" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "location_id" uuid,
    "metric_code" text,
    "value" numeric,
    "unit" text,
    "measured_at" timestamptz,
    "is_synthetic" boolean NOT NULL DEFAULT false,
    "source_type" text,
    "received_at" timestamptz,
    "quality" text,
    "verification" text,
    "event_id" text,
    CONSTRAINT "environmental_readings_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."environmental_readings" ENABLE ROW LEVEL SECURITY;
CREATE UNIQUE INDEX IF NOT EXISTS "environmental_readings_event_id_unique" ON public."environmental_readings" ("event_id") WHERE "event_id" IS NOT NULL;

-- Radiation / environment / gravity
CREATE TABLE IF NOT EXISTS public."environmental_samples" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "sample_type" text,
    "location_id" uuid,
    "sample_size" numeric,
    "collected_at" timestamptz,
    "is_synthetic" boolean NOT NULL DEFAULT false,
    "source_type" text,
    "received_at" timestamptz,
    "quality" text,
    "verification" text,
    "event_id" text,
    CONSTRAINT "environmental_samples_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."environmental_samples" ENABLE ROW LEVEL SECURITY;
CREATE UNIQUE INDEX IF NOT EXISTS "environmental_samples_event_id_unique" ON public."environmental_samples" ("event_id") WHERE "event_id" IS NOT NULL;

-- Radiation / environment / gravity
CREATE TABLE IF NOT EXISTS public."environmental_lab_results" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "sample_id" uuid,
    "test_code" text,
    "result_value" numeric,
    "unit" text,
    "verification" text,
    "is_synthetic" boolean NOT NULL DEFAULT false,
    "source_type" text,
    "received_at" timestamptz,
    "quality" text,
    "event_id" text,
    CONSTRAINT "environmental_lab_results_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."environmental_lab_results" ENABLE ROW LEVEL SECURITY;
CREATE UNIQUE INDEX IF NOT EXISTS "environmental_lab_results_event_id_unique" ON public."environmental_lab_results" ("event_id") WHERE "event_id" IS NOT NULL;

-- Radiation / environment / gravity
CREATE TABLE IF NOT EXISTS public."mission_locations" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "mission_id" uuid,
    "zone_name" text,
    "location_type" text,
    CONSTRAINT "mission_locations_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."mission_locations" ENABLE ROW LEVEL SECURITY;

-- Radiation / environment / gravity
CREATE TABLE IF NOT EXISTS public."gravity_transition_events" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "mission_id" uuid,
    "from_g" numeric,
    "to_g" numeric,
    "occurred_at" timestamptz,
    CONSTRAINT "gravity_transition_events_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."gravity_transition_events" ENABLE ROW LEVEL SECURITY;

-- Sleep / nutrition / fluids / medication
CREATE TABLE IF NOT EXISTS public."sleep_sessions" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "astronaut_id" uuid,
    "start_at" timestamptz,
    "end_at" timestamptz,
    "duration" numeric,
    "source" text,
    "is_synthetic" boolean NOT NULL DEFAULT false,
    "source_type" text,
    "received_at" timestamptz,
    "quality" text,
    "verification" text,
    "event_id" text,
    CONSTRAINT "sleep_sessions_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."sleep_sessions" ENABLE ROW LEVEL SECURITY;
CREATE UNIQUE INDEX IF NOT EXISTS "sleep_sessions_event_id_unique" ON public."sleep_sessions" ("event_id") WHERE "event_id" IS NOT NULL;

-- Sleep / nutrition / fluids / medication
CREATE TABLE IF NOT EXISTS public."behavioral_checkins" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "astronaut_id" uuid,
    "assessment_type" text,
    "score" numeric,
    "visibility_classification" text,
    "is_synthetic" boolean NOT NULL DEFAULT false,
    "source_type" text,
    "received_at" timestamptz,
    "quality" text,
    "verification" text,
    "event_id" text,
    CONSTRAINT "behavioral_checkins_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."behavioral_checkins" ENABLE ROW LEVEL SECURITY;
CREATE UNIQUE INDEX IF NOT EXISTS "behavioral_checkins_event_id_unique" ON public."behavioral_checkins" ("event_id") WHERE "event_id" IS NOT NULL;

-- Sleep / nutrition / fluids / medication
CREATE TABLE IF NOT EXISTS public."nutrition_logs" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "astronaut_id" uuid,
    "meal_at" timestamptz,
    "intake_details" jsonb,
    "is_synthetic" boolean NOT NULL DEFAULT false,
    "source_type" text,
    "received_at" timestamptz,
    "quality" text,
    "verification" text,
    "event_id" text,
    CONSTRAINT "nutrition_logs_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."nutrition_logs" ENABLE ROW LEVEL SECURITY;
CREATE UNIQUE INDEX IF NOT EXISTS "nutrition_logs_event_id_unique" ON public."nutrition_logs" ("event_id") WHERE "event_id" IS NOT NULL;

-- Sleep / nutrition / fluids / medication
CREATE TABLE IF NOT EXISTS public."fluid_balance_logs" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "astronaut_id" uuid,
    "period_start" text,
    "period_end" text,
    "intake" numeric,
    "output" numeric,
    "unit" text,
    "is_synthetic" boolean NOT NULL DEFAULT false,
    "source_type" text,
    "received_at" timestamptz,
    "quality" text,
    "verification" text,
    "event_id" text,
    CONSTRAINT "fluid_balance_logs_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."fluid_balance_logs" ENABLE ROW LEVEL SECURITY;
CREATE UNIQUE INDEX IF NOT EXISTS "fluid_balance_logs_event_id_unique" ON public."fluid_balance_logs" ("event_id") WHERE "event_id" IS NOT NULL;

-- Sleep / nutrition / fluids / medication
CREATE TABLE IF NOT EXISTS public."medication_administrations" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "astronaut_id" uuid,
    "medication_reference" text,
    "dose" numeric,
    "unit" text,
    "authorized_by" text,
    "is_synthetic" boolean NOT NULL DEFAULT false,
    "source_type" text,
    "received_at" timestamptz,
    "quality" text,
    "verification" text,
    "event_id" text,
    CONSTRAINT "medication_administrations_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."medication_administrations" ENABLE ROW LEVEL SECURITY;
CREATE UNIQUE INDEX IF NOT EXISTS "medication_administrations_event_id_unique" ON public."medication_administrations" ("event_id") WHERE "event_id" IS NOT NULL;

-- Rules / alerts / procedures / exams
CREATE TABLE IF NOT EXISTS public."health_alerts" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "rule_id" uuid,
    "astronaut_id" uuid,
    "location_id" uuid,
    "severity" text,
    "status" text,
    "is_synthetic" boolean NOT NULL DEFAULT false,
    "source_type" text,
    "received_at" timestamptz,
    "quality" text,
    "verification" text,
    "event_id" text,
    CONSTRAINT "health_alerts_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."health_alerts" ENABLE ROW LEVEL SECURITY;
CREATE UNIQUE INDEX IF NOT EXISTS "health_alerts_event_id_unique" ON public."health_alerts" ("event_id") WHERE "event_id" IS NOT NULL;

-- Rules / alerts / procedures / exams
CREATE TABLE IF NOT EXISTS public."alert_events" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "alert_id" uuid,
    "event_type" text,
    "actor_id" text,
    "occurred_at" timestamptz,
    CONSTRAINT "alert_events_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."alert_events" ENABLE ROW LEVEL SECURITY;

-- Rules / alerts / procedures / exams
CREATE TABLE IF NOT EXISTS public."alert_evidence" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "alert_id" uuid,
    "source_record_type" text,
    "source_record_id" text,
    CONSTRAINT "alert_evidence_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."alert_evidence" ENABLE ROW LEVEL SECURITY;

-- Rules / alerts / procedures / exams
CREATE TABLE IF NOT EXISTS public."alert_rules" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "version" text,
    "condition_definition" jsonb,
    "severity" text,
    "approval_status" text,
    CONSTRAINT "alert_rules_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."alert_rules" ENABLE ROW LEVEL SECURITY;

-- Rules / alerts / procedures / exams
CREATE TABLE IF NOT EXISTS public."medical_exam_schedule" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "astronaut_id" uuid,
    "exam_type" text,
    "due_at" timestamptz,
    "completion_status" text,
    CONSTRAINT "medical_exam_schedule_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."medical_exam_schedule" ENABLE ROW LEVEL SECURITY;

-- Rules / alerts / procedures / exams
CREATE TABLE IF NOT EXISTS public."medical_procedures" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "title" text,
    "version" text,
    "approval_status" text,
    "authoritative_source" text,
    CONSTRAINT "medical_procedures_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."medical_procedures" ENABLE ROW LEVEL SECURITY;

-- Rules / alerts / procedures / exams
CREATE TABLE IF NOT EXISTS public."procedure_steps" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "procedure_id" uuid,
    "step_order" text,
    "instruction" text,
    "acknowledgment_required" boolean,
    CONSTRAINT "procedure_steps_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."procedure_steps" ENABLE ROW LEVEL SECURITY;

-- Rules / alerts / procedures / exams
CREATE TABLE IF NOT EXISTS public."medical_inventory" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "item_code" text,
    "quantity" numeric,
    "expiry_at" timestamptz,
    "storage_location" text,
    CONSTRAINT "medical_inventory_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."medical_inventory" ENABLE ROW LEVEL SECURITY;

-- Rules / alerts / procedures / exams
CREATE TABLE IF NOT EXISTS public."clinical_condition_catalog" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "condition_code" text,
    "catalog_version" text,
    "description" text,
    CONSTRAINT "clinical_condition_catalog_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."clinical_condition_catalog" ENABLE ROW LEVEL SECURITY;

-- Rules / alerts / procedures / exams
CREATE TABLE IF NOT EXISTS public."recommendation_records" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "alert_id" uuid,
    "procedure_id" uuid,
    "displayed_at" timestamptz,
    "action_status" text,
    CONSTRAINT "recommendation_records_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."recommendation_records" ENABLE ROW LEVEL SECURITY;

-- Import / sync / audit
CREATE TABLE IF NOT EXISTS public."data_import_batches" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "source" text,
    "imported_at" timestamptz,
    "validation_summary" jsonb,
    CONSTRAINT "data_import_batches_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."data_import_batches" ENABLE ROW LEVEL SECURITY;

-- Import / sync / audit
CREATE TABLE IF NOT EXISTS public."sync_queue" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "event_id" text,
    "destination" text,
    "priority" text,
    "status" text,
    "attempt_count" text,
    CONSTRAINT "sync_queue_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."sync_queue" ENABLE ROW LEVEL SECURITY;

-- Import / sync / audit
CREATE TABLE IF NOT EXISTS public."sync_receipts" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "event_id" text,
    "acknowledged_at" timestamptz,
    "remote_status" text,
    CONSTRAINT "sync_receipts_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."sync_receipts" ENABLE ROW LEVEL SECURITY;

-- Import / sync / audit
CREATE TABLE IF NOT EXISTS public."audit_logs" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "actor_id" text,
    "action" text,
    "resource_type" text,
    "resource_id" text,
    "occurred_at" timestamptz,
    CONSTRAINT "audit_logs_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."audit_logs" ENABLE ROW LEVEL SECURITY;

-- Import / sync / audit
CREATE TABLE IF NOT EXISTS public."data_quality_issues" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "record_reference" text,
    "issue_type" text,
    "severity" text,
    "resolution_status" text,
    CONSTRAINT "data_quality_issues_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."data_quality_issues" ENABLE ROW LEVEL SECURITY;

-- Import / sync / audit
CREATE TABLE IF NOT EXISTS public."attachments" (
    "id" uuid NOT NULL DEFAULT gen_random_uuid(),
    "owner_record_reference" text,
    "storage_path" text,
    "hash" text,
    "access_classification" text,
    CONSTRAINT "attachments_pkey" PRIMARY KEY ("id")
);
ALTER TABLE public."attachments" ENABLE ROW LEVEL SECURITY;

-- These FKs should be executed only after checking existing live-project column types.
-- Mission assignment may be NULL for global user roles, so join uses a surrogate UUID PK.
-- On fresh DB this enforces relational integrity, without cascading history deletions.
ALTER TABLE public."mission_crew" ADD CONSTRAINT "fk_mission_crew_mission_id" FOREIGN KEY ("mission_id") REFERENCES public."missions" ("id") ON DELETE RESTRICT;
ALTER TABLE public."mission_crew" ADD CONSTRAINT "fk_mission_crew_astronaut_id" FOREIGN KEY ("astronaut_id") REFERENCES public."astronauts" ("id") ON DELETE RESTRICT;
ALTER TABLE public."user_role_assignments" ADD CONSTRAINT "fk_user_role_assignments_user_id" FOREIGN KEY ("user_id") REFERENCES public."users" ("id") ON DELETE RESTRICT;
ALTER TABLE public."user_role_assignments" ADD CONSTRAINT "fk_user_role_assignments_role_id" FOREIGN KEY ("role_id") REFERENCES public."roles" ("id") ON DELETE RESTRICT;
ALTER TABLE public."user_role_assignments" ADD CONSTRAINT "fk_user_role_assignments_mission_id" FOREIGN KEY ("mission_id") REFERENCES public."missions" ("id") ON DELETE RESTRICT;
ALTER TABLE public."device_assignments" ADD CONSTRAINT "fk_device_assignments_device_id" FOREIGN KEY ("device_id") REFERENCES public."devices" ("id") ON DELETE RESTRICT;
ALTER TABLE public."device_assignments" ADD CONSTRAINT "fk_device_assignments_astronaut_id" FOREIGN KEY ("astronaut_id") REFERENCES public."astronauts" ("id") ON DELETE RESTRICT;
ALTER TABLE public."device_assignments" ADD CONSTRAINT "fk_device_assignments_location_id" FOREIGN KEY ("location_id") REFERENCES public."mission_locations" ("id") ON DELETE RESTRICT;
ALTER TABLE public."vital_signs" ADD CONSTRAINT "fk_vital_signs_astronaut_id" FOREIGN KEY ("astronaut_id") REFERENCES public."astronauts" ("id") ON DELETE RESTRICT;
ALTER TABLE public."ecg_records" ADD CONSTRAINT "fk_ecg_records_astronaut_id" FOREIGN KEY ("astronaut_id") REFERENCES public."astronauts" ("id") ON DELETE RESTRICT;
ALTER TABLE public."symptom_reports" ADD CONSTRAINT "fk_symptom_reports_astronaut_id" FOREIGN KEY ("astronaut_id") REFERENCES public."astronauts" ("id") ON DELETE RESTRICT;
ALTER TABLE public."health_baselines" ADD CONSTRAINT "fk_health_baselines_astronaut_id" FOREIGN KEY ("astronaut_id") REFERENCES public."astronauts" ("id") ON DELETE RESTRICT;
ALTER TABLE public."medical_findings" ADD CONSTRAINT "fk_medical_findings_astronaut_id" FOREIGN KEY ("astronaut_id") REFERENCES public."astronauts" ("id") ON DELETE RESTRICT;
ALTER TABLE public."medical_incidents" ADD CONSTRAINT "fk_medical_incidents_astronaut_id" FOREIGN KEY ("astronaut_id") REFERENCES public."astronauts" ("id") ON DELETE RESTRICT;
ALTER TABLE public."medical_incidents" ADD CONSTRAINT "fk_medical_incidents_mission_id" FOREIGN KEY ("mission_id") REFERENCES public."missions" ("id") ON DELETE RESTRICT;
ALTER TABLE public."incident_events" ADD CONSTRAINT "fk_incident_events_incident_id" FOREIGN KEY ("incident_id") REFERENCES public."medical_incidents" ("id") ON DELETE RESTRICT;
ALTER TABLE public."biological_samples" ADD CONSTRAINT "fk_biological_samples_astronaut_id" FOREIGN KEY ("astronaut_id") REFERENCES public."astronauts" ("id") ON DELETE RESTRICT;
ALTER TABLE public."laboratory_results" ADD CONSTRAINT "fk_laboratory_results_sample_id" FOREIGN KEY ("sample_id") REFERENCES public."biological_samples" ("id") ON DELETE RESTRICT;
ALTER TABLE public."microbial_identifications" ADD CONSTRAINT "fk_microbial_identifications_sample_id" FOREIGN KEY ("sample_id") REFERENCES public."biological_samples" ("id") ON DELETE RESTRICT;
ALTER TABLE public."sequencing_runs" ADD CONSTRAINT "fk_sequencing_runs_sample_id" FOREIGN KEY ("sample_id") REFERENCES public."biological_samples" ("id") ON DELETE RESTRICT;
ALTER TABLE public."clinical_sample_chain" ADD CONSTRAINT "fk_clinical_sample_chain_sample_id" FOREIGN KEY ("sample_id") REFERENCES public."biological_samples" ("id") ON DELETE RESTRICT;
ALTER TABLE public."vascular_ultrasound_results" ADD CONSTRAINT "fk_vascular_ultrasound_results_astronaut_id" FOREIGN KEY ("astronaut_id") REFERENCES public."astronauts" ("id") ON DELETE RESTRICT;
ALTER TABLE public."ocular_assessments" ADD CONSTRAINT "fk_ocular_assessments_astronaut_id" FOREIGN KEY ("astronaut_id") REFERENCES public."astronauts" ("id") ON DELETE RESTRICT;
ALTER TABLE public."ocular_results" ADD CONSTRAINT "fk_ocular_results_assessment_id" FOREIGN KEY ("assessment_id") REFERENCES public."ocular_assessments" ("id") ON DELETE RESTRICT;
ALTER TABLE public."fitness_assessments" ADD CONSTRAINT "fk_fitness_assessments_astronaut_id" FOREIGN KEY ("astronaut_id") REFERENCES public."astronauts" ("id") ON DELETE RESTRICT;
ALTER TABLE public."exercise_sessions" ADD CONSTRAINT "fk_exercise_sessions_astronaut_id" FOREIGN KEY ("astronaut_id") REFERENCES public."astronauts" ("id") ON DELETE RESTRICT;
ALTER TABLE public."bone_scans" ADD CONSTRAINT "fk_bone_scans_astronaut_id" FOREIGN KEY ("astronaut_id") REFERENCES public."astronauts" ("id") ON DELETE RESTRICT;
ALTER TABLE public."bone_density_results" ADD CONSTRAINT "fk_bone_density_results_scan_id" FOREIGN KEY ("scan_id") REFERENCES public."bone_scans" ("id") ON DELETE RESTRICT;
ALTER TABLE public."functional_assessments" ADD CONSTRAINT "fk_functional_assessments_astronaut_id" FOREIGN KEY ("astronaut_id") REFERENCES public."astronauts" ("id") ON DELETE RESTRICT;
ALTER TABLE public."personal_dose_records" ADD CONSTRAINT "fk_personal_dose_records_astronaut_id" FOREIGN KEY ("astronaut_id") REFERENCES public."astronauts" ("id") ON DELETE RESTRICT;
ALTER TABLE public."radiation_area_records" ADD CONSTRAINT "fk_radiation_area_records_location_id" FOREIGN KEY ("location_id") REFERENCES public."mission_locations" ("id") ON DELETE RESTRICT;
ALTER TABLE public."environmental_readings" ADD CONSTRAINT "fk_environmental_readings_location_id" FOREIGN KEY ("location_id") REFERENCES public."mission_locations" ("id") ON DELETE RESTRICT;
ALTER TABLE public."environmental_samples" ADD CONSTRAINT "fk_environmental_samples_location_id" FOREIGN KEY ("location_id") REFERENCES public."mission_locations" ("id") ON DELETE RESTRICT;
ALTER TABLE public."environmental_lab_results" ADD CONSTRAINT "fk_environmental_lab_results_sample_id" FOREIGN KEY ("sample_id") REFERENCES public."environmental_samples" ("id") ON DELETE RESTRICT;
ALTER TABLE public."mission_locations" ADD CONSTRAINT "fk_mission_locations_mission_id" FOREIGN KEY ("mission_id") REFERENCES public."missions" ("id") ON DELETE RESTRICT;
ALTER TABLE public."gravity_transition_events" ADD CONSTRAINT "fk_gravity_transition_events_mission_id" FOREIGN KEY ("mission_id") REFERENCES public."missions" ("id") ON DELETE RESTRICT;
ALTER TABLE public."sleep_sessions" ADD CONSTRAINT "fk_sleep_sessions_astronaut_id" FOREIGN KEY ("astronaut_id") REFERENCES public."astronauts" ("id") ON DELETE RESTRICT;
ALTER TABLE public."behavioral_checkins" ADD CONSTRAINT "fk_behavioral_checkins_astronaut_id" FOREIGN KEY ("astronaut_id") REFERENCES public."astronauts" ("id") ON DELETE RESTRICT;
ALTER TABLE public."nutrition_logs" ADD CONSTRAINT "fk_nutrition_logs_astronaut_id" FOREIGN KEY ("astronaut_id") REFERENCES public."astronauts" ("id") ON DELETE RESTRICT;
ALTER TABLE public."fluid_balance_logs" ADD CONSTRAINT "fk_fluid_balance_logs_astronaut_id" FOREIGN KEY ("astronaut_id") REFERENCES public."astronauts" ("id") ON DELETE RESTRICT;
ALTER TABLE public."medication_administrations" ADD CONSTRAINT "fk_medication_administrations_astronaut_id" FOREIGN KEY ("astronaut_id") REFERENCES public."astronauts" ("id") ON DELETE RESTRICT;
ALTER TABLE public."health_alerts" ADD CONSTRAINT "fk_health_alerts_astronaut_id" FOREIGN KEY ("astronaut_id") REFERENCES public."astronauts" ("id") ON DELETE RESTRICT;
ALTER TABLE public."health_alerts" ADD CONSTRAINT "fk_health_alerts_location_id" FOREIGN KEY ("location_id") REFERENCES public."mission_locations" ("id") ON DELETE RESTRICT;
ALTER TABLE public."health_alerts" ADD CONSTRAINT "fk_health_alerts_rule_id" FOREIGN KEY ("rule_id") REFERENCES public."alert_rules" ("id") ON DELETE RESTRICT;
ALTER TABLE public."alert_events" ADD CONSTRAINT "fk_alert_events_alert_id" FOREIGN KEY ("alert_id") REFERENCES public."health_alerts" ("id") ON DELETE RESTRICT;
ALTER TABLE public."alert_evidence" ADD CONSTRAINT "fk_alert_evidence_alert_id" FOREIGN KEY ("alert_id") REFERENCES public."health_alerts" ("id") ON DELETE RESTRICT;
ALTER TABLE public."medical_exam_schedule" ADD CONSTRAINT "fk_medical_exam_schedule_astronaut_id" FOREIGN KEY ("astronaut_id") REFERENCES public."astronauts" ("id") ON DELETE RESTRICT;
ALTER TABLE public."procedure_steps" ADD CONSTRAINT "fk_procedure_steps_procedure_id" FOREIGN KEY ("procedure_id") REFERENCES public."medical_procedures" ("id") ON DELETE RESTRICT;
ALTER TABLE public."recommendation_records" ADD CONSTRAINT "fk_recommendation_records_alert_id" FOREIGN KEY ("alert_id") REFERENCES public."health_alerts" ("id") ON DELETE RESTRICT;
ALTER TABLE public."recommendation_records" ADD CONSTRAINT "fk_recommendation_records_procedure_id" FOREIGN KEY ("procedure_id") REFERENCES public."medical_procedures" ("id") ON DELETE RESTRICT;
COMMIT;
