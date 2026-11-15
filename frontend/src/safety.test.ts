import { describe, it, expect, vi } from "vitest";
import { initialSnapshot } from "./seed";
import {
  applyScenario,
  scopedSnapshot,
  persistMock,
  readMock,
  event,
} from "./service";
import { canAccess, comparable, displayValue, symptomSchema } from "./types";
import catalog from "./catalog.json";
describe("PDF safety and scenario requirements", () => {
  it("includes all canonical table and feature identifiers", () => {
    expect(catalog.tables).toHaveLength(57);
    expect(new Set(catalog.tables.map((t) => t.name)).size).toBe(57);
    expect(catalog.features).toHaveLength(47);
  });
  it("S01 has four fictional astronauts and no alert", () => {
    expect(initialSnapshot().crew).toHaveLength(4);
    expect(initialSnapshot().alerts).toHaveLength(0);
  });
  it("S02 does not treat workout HR as an abnormal resting measurement", () => {
    const s = initialSnapshot(),
      r = applyScenario(s, "S02", s.crew[0].id);
    expect(r.measurements[0].value).toBe(128);
    expect(r.alerts).toHaveLength(0);
  });
  it("S03 missing SpO2 remains null while severe symptom creates incident", () => {
    const s = initialSnapshot(),
      r = applyScenario(s, "S03", s.crew[0].id);
    const spo2 = r.measurements.find((x) => x.metric_code === "SpO2")!;
    expect(spo2.value).toBeNull();
    expect(displayValue(spo2)).toBe("Unavailable");
    expect(r.alerts[0].severity).toBe("critical");
    expect(r.alerts[0].incident_id).toBeTruthy();
  });
  it("S04 has a single correlated incident with window and rule version", () => {
    const s = initialSnapshot(),
      r = applyScenario(s, "S04", s.crew[0].id);
    expect(r.alerts).toHaveLength(1);
    expect(r.alerts[0].evidence.join()).toContain("1 h");
    expect(r.alerts[0].rule_version).toBe(1);
  });
  it("S05 unreviewed D-dimer has no clot diagnosis", () => {
    const s = initialSnapshot(),
      r = applyScenario(s, "S05", s.crew[0].id);
    expect(r.alerts[0].severity).toBe("advisory");
    expect(r.alerts[0].evidence.join()).toContain(
      "No automated thrombus diagnosis",
    );
  });
  it("S06 retains side specificity", () => {
    const s = initialSnapshot(),
      r = applyScenario(s, "S06", s.crew[0].id);
    const rows = r.records.filter(
      (x) =>
        x.astronaut_id === s.crew[0].id &&
        x.table === "vascular_ultrasound_results",
    );
    expect(rows.find((x) => x.details.side === "left")!.status).toBe(
      "Demo clinician reviewed",
    );
    expect(rows.find((x) => x.details.side === "right")!.status).toBe(
      "Pending",
    );
    expect(comparable(rows[0], rows[1])).toBe(false);
  });
  it("S07 stale personal dose remains separate from absorbed area dose", () => {
    const s = initialSnapshot(),
      r = applyScenario(s, "S07", s.crew[0].id);
    expect(
      r.records.find((x) => x.table === "personal_dose_records")!.status,
    ).toBe("Stale");
    expect(
      comparable(
        r.records.find((x) => x.table === "personal_dose_records")!,
        r.records.find((x) => x.table === "radiation_area_records")!,
      ),
    ).toBe(false);
  });
  it("S08 no in-flight BMD is invented", () => {
    const s = initialSnapshot(),
      r = applyScenario(s, "S08", s.crew[0].id);
    expect(
      r.records
        .filter((x) => x.domain === "Bone")
        .every((x) => x.details.phase !== "inflight"),
    ).toBe(true);
  });
  it("S09 microbial method and denominator stay attached", () => {
    const s = initialSnapshot(),
      r = applyScenario(s, "S09", s.crew[0].id);
    expect(r.alerts[0].evidence.join()).toContain("CFU/100 mL");
    expect(r.alerts[0].evidence.join()).toContain("Membrane filtration");
  });
  it("S10 queued demo event survives serialized reload with immutable identity", () => {
    const map = new Map();
    vi.stubGlobal("localStorage", {
      setItem: (k: string, v: string) => map.set(k, v),
      getItem: (k: string) => map.get(k),
    });
    const s = initialSnapshot();
    s.events = [event("symptom_reports", { astronaut_id: s.subject_id }, true)];
    persistMock(s);
    const r = readMock();
    expect(r.events[0].event_id).toBe(s.events[0].event_id);
    expect(r.events[0].status).toBe("queued");
    vi.unstubAllGlobals();
  });
  it("S11 expires guidance instead of issuing treatment", () => {
    const s = initialSnapshot(),
      r = applyScenario(s, "S11", s.crew[0].id);
    expect(
      r.records
        .filter((x) => x.table === "medical_procedures")
        .every((x) => x.details.approval_status === "expired"),
    ).toBe(true);
    expect(r.alerts[0].severity).toBe("data-unavailable");
  });
  it("S12 creates denied-access audit without confidential contents", () => {
    const s = initialSnapshot(),
      r = applyScenario(s, "S12", s.crew[0].id);
    expect(
      r.events.some(
        (x) =>
          x.entity_type === "audit_denied" && x.payload.result === "denied",
      ),
    ).toBe(true);
    expect(canAccess("mission_operator", "self")).toBe(false);
  });
  it("crew cannot see other crew medical data; operator sees no vital values", () => {
    const s = initialSnapshot(),
      r = scopedSnapshot(s, "crew");
    expect(r.crew).toHaveLength(1);
    expect(r.measurements.every((m) => m.astronaut_id === s.subject_id)).toBe(
      true,
    );
    expect(scopedSnapshot(s, "mission_operator").measurements).toHaveLength(0);
  });
  it("rejects invalid severity and oversized symptom notes", () => {
    expect(
      symptomSchema.safeParse({
        astronaut_id: "1",
        symptom_code: "headache",
        severity: "unknown",
        onset_at: "today",
        notes: "x".repeat(1001),
        is_synthetic: true,
      }).success,
    ).toBe(false);
  });
  it("new emergencies remain distinct", () => {
    const s = initialSnapshot(),
      a = applyScenario(s, "S03", s.subject_id),
      b = applyScenario(a, "S03", s.subject_id);
    expect(b.alerts).toHaveLength(2);
    expect(b.alerts[0].incident_id).not.toBe(b.alerts[1].incident_id);
  });
});
