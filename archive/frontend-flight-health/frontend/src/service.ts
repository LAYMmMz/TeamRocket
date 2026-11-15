import { initialSnapshot, SIM_TIME } from "./seed";
import {
  symptomSchema,
  measurementSchema,
  alertSchema,
  type Snapshot,
  type Symptom,
  type Role,
  type Alert,
  type Event,
} from "./types";
export const isMock = import.meta.env.VITE_DATA_MODE !== "api";
const key = "teamrocket-demo-v1";
export function readMock(): Snapshot {
  try {
    const saved = JSON.parse(localStorage.getItem(key) || "null");
    if (saved?.crew?.length === 4 && Array.isArray(saved.events)) return saved;
  } catch {}
  return initialSnapshot();
}
export function persistMock(s: Snapshot) {
  if (isMock) localStorage.setItem(key, JSON.stringify(s));
}
let token: string | null = null;
export function setAccessToken(value: string | null) {
  token = value;
}
async function request(
  path: string,
  method = "GET",
  body?: unknown,
  eventId?: string,
) {
  const base = import.meta.env.VITE_API_BASE_URL;
  if (!base)
    throw new Error(
      "VITE_API_BASE_URL is missing. Configure the backend URL and rebuild.",
    );
  if (!token)
    throw new Error(
      "Sign in is required. Supply a Supabase access token using the integration panel.",
    );
  const response = await fetch(`${base.replace(/\/$/, "")}${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      ...(body ? { "Content-Type": "application/json" } : {}),
      ...(eventId ? { "Idempotency-Key": eventId } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
    signal: AbortSignal.timeout(15000),
  });
  if (!response.ok)
    throw new Error(
      `Backend request failed (${response.status}). No success was recorded.`,
    );
  return response.status === 204 ? null : response.json();
}
export async function loadSnapshot(): Promise<Snapshot> {
  if (isMock) return readMock();
  const d = await request("/reports/dashboard");
  if (
    !d ||
    !Array.isArray(d.crew) ||
    !Array.isArray(d.records) ||
    !Array.isArray(d.events) ||
    ![
      "crew",
      "crew_medical_officer",
      "ground_clinician",
      "mission_operator",
      "administrator",
    ].includes(d.role) ||
    typeof d.subject_id !== "string"
  )
    throw new Error("Invalid dashboard response");
  d.measurements = d.measurements.map((x: unknown) =>
    measurementSchema.parse(x),
  );
  d.alerts = d.alerts.map((x: unknown) => alertSchema.parse(x));
  return d;
}
export async function submitSymptom(input: Symptom, eventId: string) {
  const parsed = symptomSchema.parse(input);
  if (!isMock)
    await request(
      "/symptoms",
      "POST",
      { ...parsed, event_id: eventId },
      eventId,
    );
}
export async function acknowledge(id: string, eventId: string) {
  if (!isMock)
    await request(
      `/alerts/${encodeURIComponent(id)}/acknowledgments`,
      "POST",
      { event_id: eventId },
      eventId,
    );
}
export async function sendReview(id: string, note: string, eventId: string) {
  if (!isMock)
    await request(
      `/reports/${encodeURIComponent(id)}/reviews`,
      "POST",
      { note, event_id: eventId },
      eventId,
    );
}
export function event(
  entity_type: string,
  payload: Record<string, unknown>,
  offline = false,
): Event {
  return {
    event_id: crypto.randomUUID(),
    entity_type,
    payload,
    occurred_at: isMock ? SIM_TIME : new Date().toISOString(),
    status: offline ? "queued" : "received",
  };
}
export function newAlert(
  astronaut_id: string | null,
  title: string,
  severity: Alert["severity"],
  evidence: string[],
  scenario: string,
): Alert {
  return {
    id: crypto.randomUUID(),
    astronaut_id,
    location_id: astronaut_id ? null : "habitat",
    title,
    severity,
    status: "open",
    rule_id: `DEMO-${scenario}`,
    rule_version: 1,
    approval_status: "approved_for_demo",
    evidence,
    created_at: SIM_TIME,
    acknowledged_at: null,
    incident_id: crypto.randomUUID(),
    is_synthetic: true,
  };
}
export function applyScenario(
  s: Snapshot,
  id: string,
  crewId: string,
): Snapshot {
  const next = structuredClone(s);
  const values = next.measurements.filter((m) => m.astronaut_id === crewId);
  const add = (
    title: string,
    severity: Alert["severity"],
    evidence: string[],
    global = false,
  ) => {
    next.alerts.unshift(
      newAlert(global ? null : crewId, title, severity, evidence, id),
    );
  };
  if (id === "S01") return { ...initialSnapshot(), role: s.role };
  if (id === "S02") {
    values.find((m) => m.metric_code === "HR")!.value = 128;
    next.events.unshift(
      event("exercise_context", {
        astronaut_id: crewId,
        note: "HR 128 bpm during workout; no resting alert",
      }),
    );
  }
  if (id === "S03") {
    Object.assign(
      values.find((m) => m.metric_code === "SpO2")!,
      { value: null, quality: "missing" },
    );
    add("Serious breathing symptom", "critical", [
      "Crew self-report: severe breathing difficulty",
      "SpO2 unavailable; no imputed measurement",
    ]);
  }
  if (id === "S04") {
    next.records
      .filter((r) => r.title === "Carbon dioxide")
      .forEach((r) => {
        r.value = "5.2";
        r.details.averaging_window = "1 hour";
      });
    add(
      "Cabin CO₂ · symptom correlation",
      "warning",
      [
        "DEMO-CO2-01: 5.2 mmHg / 1 h",
        "Crew headache report",
        "Demo criterion only; not clinically validated",
      ],
      true,
    );
  }
  if (id === "S05")
    add("D-dimer requires clinical review", "advisory", [
      "0.61 mg/L FEU · DEMO assay A",
      "No automated thrombus diagnosis",
    ]);
  if (id === "S06") {
    const r = next.records.find(
      (r) => r.astronaut_id === crewId && r.title.includes("Doppler · left"),
    )!;
    r.status = "Demo clinician reviewed";
    r.details.reviewed_by = "Synthetic clinician";
    add("Left jugular finding available", "informational", [
      r.id,
      "Left side only; right side unchanged",
    ]);
  }
  if (id === "S07") {
    next.records
      .filter(
        (r) => r.table === "personal_dose_records" && r.astronaut_id === crewId,
      )
      .forEach((r) => {
        r.status = "Stale";
        r.measured_at = "2026-06-12T12:00:00Z";
      });
    add(
      "SPE scenario · stale personal dosimeter",
      "warning",
      [
        "Synthetic SPE source",
        "Personal dose stale; accumulation unavailable",
        "Review demo shelter location",
      ],
      true,
    );
  }
  if (id === "S08")
    add("OCT examination due", "informational", [
      "OCT left/right due 16 June",
      "DXA unavailable in flight; pre/postflight only",
    ]);
  if (id === "S09")
    add(
      "Water culture requires review",
      "advisory",
      ["12 CFU/100 mL", "Membrane filtration demo", "Re-sampling requested"],
      true,
    );
  if (id === "S11") {
    next.records
      .filter((r) => r.table === "medical_procedures")
      .forEach((r) => {
        r.status = "Expired — unavailable operationally";
        r.details.approval_status = "expired";
        r.details.expires_at = "2026-06-01";
      });
    add("Procedure expired · guidance blocked", "data-unavailable", [
      "Historical reference only",
      "Unapproved research rules cannot trigger treatment guidance",
    ]);
  }
  if (id === "S12")
    next.events.unshift(
      event("audit_denied", {
        resource: "behavioral_checkins",
        actor_role: "mission_operator",
        result: "denied",
        notes: "Confidential content not returned",
      }),
    );
  next.events.unshift(
    event("scenario", { scenario: id, astronaut_id: crewId }),
  );
  return next;
}
export function scopedSnapshot(s: Snapshot, role: Role): Snapshot {
  if (role === "crew")
    return {
      ...s,
      crew: s.crew.filter((c) => c.id === s.subject_id),
      measurements: s.measurements.filter(
        (m) => m.astronaut_id === s.subject_id,
      ),
      records: s.records.filter(
        (r) => r.astronaut_id === null || r.astronaut_id === s.subject_id,
      ),
      alerts: s.alerts.filter(
        (a) => a.astronaut_id === null || a.astronaut_id === s.subject_id,
      ),
      events: s.events.filter(
        (e) =>
          e.payload.astronaut_id === s.subject_id &&
          e.entity_type !== "behavioral_checkins",
      ),
    };
  if (role === "mission_operator")
    return {
      ...s,
      measurements: [],
      records: s.records.filter((r) => r.astronaut_id === null),
      events: s.events.filter(
        (e) =>
          !["behavioral_checkins", "symptom_reports"].includes(e.entity_type),
      ),
      alerts: s.alerts.map((a) => ({
        ...a,
        title: a.astronaut_id ? "Crew medical attention required" : a.title,
        evidence: a.astronaut_id ? ["Restricted to clinical role"] : a.evidence,
      })),
    };
  return s;
}
