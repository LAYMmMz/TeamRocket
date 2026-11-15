create extension if not exists "uuid-ossp";

create table public.astronauts (
    id uuid primary key default gen_random_uuid(),
    full_name text not null,
    callsign text,
    assigned_role text,
    created_at timestamptz default timezone('utc', now()) not null
);

create table public.health_logs (
    id uuid primary key default gen_random_uuid(),
    astronaut_id uuid not null references public.astronauts(id) on delete restrict,
    mission_id text not null,
    source_device_id text,
    source_type text default 'Automated Telemetry',
    measured_at timestamptz not null,
    received_at timestamptz default timezone('utc', now()) not null,
    original_value numeric,
    original_unit text,
    normalized_value numeric,
    normalized_unit text,
    quality_status text default 'Unknown',
    verification_status text default 'Unverified',
    clinical_review_state text default 'Unreviewed',
    audit_context jsonb,
    gravity_level numeric,
    systolic_blood_pressure integer,
    diastolic_blood_pressure integer,
    heart_rate integer,
    nausea_level integer,
    readiness_status text
);

create table public.personal_dose_records (
    id uuid primary key default gen_random_uuid(),
    astronaut_id uuid not null references public.astronauts(id) on delete restrict,
    mission_id text not null,
    measured_at timestamptz not null,
    original_value numeric,
    original_unit text,
    quality_status text default 'Unknown',
    verification_status text default 'Unverified'
);

create table public.radiation_area_records (
    id uuid primary key default gen_random_uuid(),
    mission_id text not null,
    compartment_name text not null,
    measured_at timestamptz not null,
    original_value numeric,
    original_unit text
);

create table public.environmental_readings (
    id uuid primary key default gen_random_uuid(),
    mission_id text not null,
    parameter_name text not null,
    measured_at timestamptz not null,
    original_value numeric,
    original_unit text
);

create table public.sleep_sessions (
    id uuid primary key default gen_random_uuid(),
    astronaut_id uuid not null references public.astronauts(id) on delete restrict,
    start_at timestamptz not null,
    end_at timestamptz not null,
    original_value numeric,
    original_unit text default 'minutes'
);

create table public.nutrition_logs (
    id uuid primary key default gen_random_uuid(),
    astronaut_id uuid not null references public.astronauts(id) on delete restrict,
    measured_at timestamptz not null,
    original_value numeric,
    original_unit text default 'kcal',
    intake_details jsonb
);

create table public.fluid_balance_logs (
    id uuid primary key default gen_random_uuid(),
    astronaut_id uuid not null references public.astronauts(id) on delete restrict,
    period_start timestamptz not null,
    period_end timestamptz not null,
    original_value numeric,
    original_unit text
);

alter table public.astronauts enable row level security;
alter table public.health_logs enable row level security;
alter table public.personal_dose_records enable row level security;
alter table public.radiation_area_records enable row level security;
alter table public.environmental_readings enable row level security;
alter table public.sleep_sessions enable row level security;
alter table public.nutrition_logs enable row level security;
alter table public.fluid_balance_logs enable row level security;

create policy "Enable read access for authenticated and anon users" on public.health_logs for select using (true);
create policy "Enable read access for astronauts" on public.astronauts for select using (true);
create policy "Enable read access for personal doses" on public.personal_dose_records for select using (true);
create policy "Enable read access for radiation area" on public.radiation_area_records for select using (true);
create policy "Enable read access for environmental" on public.environmental_readings for select using (true);
create policy "Enable read access for sleep" on public.sleep_sessions for select using (true);
create policy "Enable read access for nutrition" on public.nutrition_logs for select using (true);
create policy "Enable read access for fluid balance" on public.fluid_balance_logs for select using (true);