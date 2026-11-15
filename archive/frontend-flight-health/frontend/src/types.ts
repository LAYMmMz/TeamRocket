import { z } from "zod";
export type Role =
  | "crew"
  | "crew_medical_officer"
  | "ground_clinician"
  | "mission_operator"
  | "administrator";
export type View =
  | "command"
  | "astronaut"
  | "exams"
  | "environment"
  | "laboratory"
  | "self"
  | "ground"
  | "operations"
  | "research"
  | "data";
export const measurementSchema = z.object({
  id: z.string(),
  astronaut_id: z.string(),
  metric_code: z.string(),
  value: z.number().nullable(),
  unit: z.string(),
  measured_at: z.string().datetime(),
  received_at: z.string().datetime(),
  source_device_id: z.string(),
  quality: z.enum(["valid", "suspect", "missing", "stale"]),
  verification: z.string(),
  is_synthetic: z.boolean(),
  baseline_value: z.number().nullable(),
  history: z.array(z.number()),
});
export type Measurement = z.infer<typeof measurementSchema>;
export const alertSchema = z.object({
  id: z.string(),
  astronaut_id: z.string().nullable(),
  location_id: z.string().nullable(),
  title: z.string(),
  severity: z.enum([
    "informational",
    "advisory",
    "warning",
    "critical",
    "data-unavailable",
  ]),
  status: z.enum(["open", "acknowledged", "resolved"]),
  rule_id: z.string(),
  rule_version: z.number(),
  approval_status: z.string(),
  evidence: z.array(z.string()),
  created_at: z.string(),
  acknowledged_at: z.string().nullable(),
  incident_id: z.string(),
  is_synthetic: z.boolean(),
});
export type Alert = z.infer<typeof alertSchema>;
export type Crew = {
  id: string;
  crew_code: string;
  display_name: string;
  crew_role: string;
  color: string;
};
export type DomainRecord = {
  id: string;
  astronaut_id: string | null;
  domain: string;
  title: string;
  table: string;
  value: string;
  unit: string;
  method: string;
  status: string;
  measured_at: string;
  source: string;
  details: Record<string, string>;
  is_synthetic: boolean;
};
export type Event = {
  event_id: string;
  entity_type: string;
  occurred_at: string;
  status: "queued" | "received";
  payload: Record<string, unknown>;
};
export type Snapshot = {
  crew: Crew[];
  measurements: Measurement[];
  alerts: Alert[];
  records: DomainRecord[];
  events: Event[];
  role: Role;
  subject_id: string;
  simulation_time: string;
};
export const symptomSchema = z.object({
  astronaut_id: z.string().min(1),
  symptom_code: z.string().min(1),
  severity: z.enum(["mild", "moderate", "severe"]),
  onset_at: z.string().datetime(),
  notes: z.string().max(1000),
  is_synthetic: z.boolean(),
});
export type Symptom = z.infer<typeof symptomSchema>;
export const access: Record<View, Role[]> = {
  command: [
    "crew_medical_officer",
    "ground_clinician",
    "mission_operator",
    "administrator",
  ],
  astronaut: [
    "crew",
    "crew_medical_officer",
    "ground_clinician",
    "administrator",
  ],
  exams: ["crew_medical_officer", "ground_clinician", "administrator"],
  environment: [
    "crew",
    "crew_medical_officer",
    "ground_clinician",
    "mission_operator",
    "administrator",
  ],
  laboratory: ["crew_medical_officer", "ground_clinician", "administrator"],
  self: ["crew", "crew_medical_officer", "administrator"],
  ground: ["ground_clinician", "administrator"],
  operations: ["crew_medical_officer", "ground_clinician", "administrator"],
  research: ["crew_medical_officer", "ground_clinician", "administrator"],
  data: ["administrator"],
};
export function canAccess(role: Role, view: View) {
  return access[view].includes(role);
}
export function displayValue(m: Measurement) {
  return m.value === null ? "Unavailable" : String(m.value);
}
export function comparable(a: DomainRecord, b: DomainRecord) {
  return (
    a.table === b.table &&
    a.unit === b.unit &&
    a.method === b.method &&
    ["eye", "side", "bone_region", "dose_quantity"].every(
      (k) => a.details[k] === b.details[k],
    )
  );
}
