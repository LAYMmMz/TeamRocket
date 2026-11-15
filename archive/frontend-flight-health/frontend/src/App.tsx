import { useEffect, useState, type FormEvent } from "react";
import {
  Activity,
  Orbit,
  Users,
  HeartPulse,
  Stethoscope,
  Radiation,
  FlaskConical,
  ClipboardList,
  Radio,
  Shield,
  Database,
  ChevronRight,
  Bell,
  Wifi,
  WifiOff,
  Volume2,
  VolumeX,
  ArrowUpRight,
  Check,
  Search,
  Download,
  X,
  RotateCcw,
  Menu,
} from "lucide-react";
import Astronaut from "./Astronaut";
import { initialSnapshot, scenarios, SIM_TIME } from "./seed";
import {
  isMock,
  loadSnapshot,
  persistMock,
  applyScenario,
  scopedSnapshot,
  event,
  newAlert,
  submitSymptom,
  acknowledge,
  sendReview,
  setAccessToken,
} from "./service";
import {
  canAccess,
  displayValue,
  type View,
  type Role,
  type Snapshot,
  type DomainRecord,
  type Alert,
  type Measurement,
} from "./types";
import catalog from "./catalog.json";
const nav: { id: View; label: string; icon: typeof Activity; group: string }[] =
  [
    { id: "command", label: "Mission command", icon: Orbit, group: "MONITOR" },
    {
      id: "astronaut",
      label: "Astronaut health",
      icon: HeartPulse,
      group: "MONITOR",
    },
    {
      id: "exams",
      label: "Exams & recovery",
      icon: Stethoscope,
      group: "MONITOR",
    },
    {
      id: "environment",
      label: "Radiation & habitat",
      icon: Radiation,
      group: "MONITOR",
    },
    {
      id: "laboratory",
      label: "Laboratory & immune",
      icon: FlaskConical,
      group: "MONITOR",
    },
    {
      id: "self",
      label: "Crew self-assessment",
      icon: ClipboardList,
      group: "OPERATIONS",
    },
    {
      id: "ground",
      label: "Ground medical review",
      icon: Radio,
      group: "OPERATIONS",
    },
    {
      id: "operations",
      label: "Medical resources",
      icon: Shield,
      group: "OPERATIONS",
    },
    {
      id: "research",
      label: "Research & sources",
      icon: Activity,
      group: "SYSTEM",
    },
    { id: "data", label: "Data & coverage", icon: Database, group: "SYSTEM" },
  ];
const title: Record<View, string> = {
  command: "Every crew member. Every signal.",
  astronaut: "Individual astronaut health",
  exams: "Clinical examinations & recovery",
  environment: "Radiation & cabin environment",
  laboratory: "Laboratory & immune health",
  self: "Your health. Your voice.",
  ground: "Ground medical review",
  operations: "Medical operations & resources",
  research: "Research with clear boundaries",
  data: "One mission. One data contract.",
};
const sub: Record<View, string> = {
  command: "A connected picture of crew health, from orbit to ground.",
  astronaut:
    "Personal baselines, observations, and longitudinal health records.",
  exams: "Side-specific findings and method-aware examination review.",
  environment:
    "Understand exposure, habitat conditions, and environmental samples.",
  laboratory: "Follow each specimen from collection through verified review.",
  self: "Report symptoms and complete a private check-in with your medical team.",
  ground: "Review received evidence and follow the incident timeline.",
  operations:
    "Versioned guidance, inventory, and mission-aware medical support.",
  research: "Source-controlled definitions. No invented clinical models.",
  data: "Traceability to the final 13-page development specification.",
};
function stamp(t: string) {
  return (
    new Date(t).toLocaleString("en-GB", {
      timeZone: "UTC",
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    }) + " UTC"
  );
}
function Tag({
  children,
  tone = "neutral",
}: {
  children: React.ReactNode;
  tone?: string;
}) {
  return <span className={`tag ${tone}`}>{children}</span>;
}
function Spark({
  values,
  color = "#8fe5d3",
}: {
  values: number[];
  color?: string;
}) {
  const min = Math.min(...values) - 2,
    max = Math.max(...values) + 2;
  return (
    <svg
      viewBox="0 0 240 56"
      className="spark"
      role="img"
      aria-label="Synthetic 30-day trend"
    >
      <path
        d={`M ${values.map((v, i) => `${(i * 240) / (values.length - 1)},${52 - ((v - min) / (max - min)) * 48}`).join(" L ")}`}
        stroke={color}
        fill="none"
        strokeWidth="2"
      />
    </svg>
  );
}
function Metric({ m, onClick }: { m: Measurement; onClick: () => void }) {
  return (
    <button className="metric panel" onClick={onClick}>
      <span>
        {m.metric_code}
        <Activity size={14} />
      </span>
      <strong>
        {displayValue(m)} <small>{m.value === null ? "" : m.unit}</small>
      </strong>
      <Spark values={m.history} />
      <footer>
        {m.quality === "valid" ? "Demo fixture" : m.quality.toUpperCase()} ·{" "}
        {stamp(m.measured_at)}
        <br />
        {m.source_device_id} · {m.is_synthetic ? "SIMULATED" : "ACTUAL"}
      </footer>
    </button>
  );
}
export default function App() {
  const [state, setState] = useState<Snapshot>(() =>
      isMock
        ? initialSnapshot()
        : {
            ...initialSnapshot(),
            crew: [],
            measurements: [],
            alerts: [],
            records: [],
            events: [],
          },
    ),
    [view, setView] = useState<View>("command"),
    [selected, setSelected] = useState(initialSnapshot().crew[0].id),
    [detail, setDetail] = useState<DomainRecord | Measurement | Alert | null>(
      null,
    ),
    [offline, setOffline] = useState(false),
    [sound, setSound] = useState(false),
    [notice, setNotice] = useState(""),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(true),
    [search, setSearch] = useState(""),
    [scenario, setScenario] = useState("S03"),
    [menu, setMenu] = useState(false),
    [range, setRange] = useState("30"),
    [busy, setBusy] = useState(false),
    [integration, setIntegration] = useState(false),
    [apiReady, setApiReady] = useState(isMock);
  const [audio, setAudio] = useState<AudioContext | null>(null);
  async function reload() {
    setLoading(true);
    setError("");
    try {
      const s = await loadSnapshot();
      setState(s);
      setApiReady(true);
      setSelected(s.subject_id);
      if (!canAccess(s.role, view))
        setView(s.role === "crew" ? "self" : "environment");
    } catch (e) {
      setApiReady(false);
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    reload();
    return () => {
      audio?.close();
    };
  }, []);
  useEffect(() => {
    if (!loading && isMock) persistMock(state);
  }, [state, loading]);
  useEffect(() => {
    if (!isMock) {
      const timer = setInterval(() => reload(), 30000);
      return () => clearInterval(timer);
    }
  }, []);
  useEffect(() => {
    if (!notice) return;
    const t = setTimeout(() => setNotice(""), 6000);
    return () => clearTimeout(t);
  }, [notice]);
  const s = scopedSnapshot(state, state.role),
    crew = s.crew.find((c) => c.id === selected) || s.crew[0],
    open = s.alerts.filter((a) => a.status === "open"),
    myVitals = s.measurements.filter((m) => m.astronaut_id === crew?.id),
    records = s.records.filter(
      (r) => r.astronaut_id === null || r.astronaut_id === crew?.id,
    ),
    queued = s.events.filter((e) => e.status === "queued");
  useEffect(() => {
    if (
      sound &&
      audio &&
      open.some((a) => a.severity === "critical" || a.severity === "warning")
    ) {
      const beep = () => {
        const o = audio.createOscillator(),
          g = audio.createGain();
        o.connect(g);
        g.connect(audio.destination);
        o.frequency.value = 660;
        g.gain.setValueAtTime(0.055, audio.currentTime);
        g.gain.exponentialRampToValueAtTime(0.001, audio.currentTime + 0.4);
        o.start();
        o.stop(audio.currentTime + 0.4);
      };
      beep();
      const t = setInterval(beep, 6000);
      return () => clearInterval(t);
    }
  }, [sound, audio, open.map((a) => a.id).join(",")]);
  function go(v: View) {
    if (!canAccess(state.role, v)) {
      setError("Access denied for this role.");
      return;
    }
    setView(v);
    window.scrollTo({ top: 0, behavior: "instant" });
    setSearch("");
    setMenu(false);
  }
  function role(r: Role) {
    setState((old) => ({ ...old, role: r }));
    setDetail(null);
    setSelected(state.subject_id);
    if (!canAccess(r, view)) setView(r === "crew" ? "self" : "command");
  }
  function run() {
    if (scenario === "S10") {
      setOffline(true);
      setNotice(
        "Demo disconnected. New actions will persist locally as queued demo events.",
      );
      setState((old) => ({
        ...old,
        events: [
          event("offline_start", { note: "Demo disconnection" }, true),
          ...old.events,
        ],
      }));
      return;
    }
    setState((old) => applyScenario(old, scenario, crew.id));
    setNotice(
      `${scenario} applied to ${crew.display_name}. All effects are simulated.`,
    );
  }
  async function ack(a: Alert) {
    setBusy(true);
    try {
      const e = event(
        "alert_acknowledgment",
        { alert_id: a.id, astronaut_id: a.astronaut_id },
        offline,
      );
      await acknowledge(a.id, e.event_id);
      setState((old) => ({
        ...old,
        alerts: old.alerts.map((x) =>
          x.id === a.id
            ? { ...x, status: "acknowledged", acknowledged_at: SIM_TIME }
            : x,
        ),
        events: [e, ...old.events],
      }));
      setDetail(null);
      if (!isMock) await reload();
      setNotice("Acknowledged. The incident remains open for clinical review.");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function report(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    const form = e.currentTarget,
      d = new FormData(form),
      severity = d.get("severity") as "mild" | "moderate" | "severe";
    const payload = {
      astronaut_id: crew.id,
      symptom_code: String(d.get("symptom")),
      severity,
      onset_at: new Date(String(d.get("onset")) + "Z").toISOString(),
      notes: String(d.get("notes")),
      is_synthetic: isMock,
    };
    try {
      const ev = event("symptom_reports", payload, offline);
      await submitSymptom(payload, ev.event_id);
      if (isMock)
        setState((old) => ({
          ...old,
          events: [ev, ...old.events],
          alerts:
            severity === "severe"
              ? [
                  newAlert(
                    crew.id,
                    "Severe self-reported symptom",
                    "critical",
                    [
                      `${payload.symptom_code}: severe`,
                      "Manual report; no diagnosis inferred",
                    ],
                    "SYMPTOM",
                  ),
                  ...old.alerts,
                ]
              : old.alerts,
        }));
      else await reload();
      form.reset();
      setNotice(
        isMock
          ? "Simulated report saved. Severe symptoms create a demo incident."
          : "Report accepted by backend.",
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  function checkin(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = e.currentTarget,
      d = new FormData(f);
    const ev = event(
      "behavioral_checkins",
      {
        astronaut_id: crew.id,
        assessment_type: "private_checkin",
        score: Number(d.get("fatigue")),
        notes: String(d.get("private")),
        visibility_classification: "confidential",
      },
      offline,
    );
    setState((old) => ({ ...old, events: [ev, ...old.events] }));
    setNotice(
      "Private demo check-in saved. Demo storage is for fictional data only.",
    );
    f.reset();
  }
  function reconnect() {
    setOffline(false);
    setState((old) => ({
      ...old,
      events: old.events.map((e) =>
        e.status === "queued" ? { ...e, status: "received" } : e,
      ),
    }));
    setNotice(
      "Demo receipt simulation completed. No events were sent to a real backend.",
    );
  }
  function exportData() {
    const blob = new Blob([JSON.stringify(s, null, 2)], {
        type: "application/json",
      }),
      url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "TeamRocket-simulated-mission.json";
    a.click();
    URL.revokeObjectURL(url);
  }
  const filtered = (domains: string[]) =>
    records.filter(
      (r) =>
        domains.includes(r.domain) &&
        `${r.title} ${r.value} ${r.method}`
          .toLowerCase()
          .includes(search.toLowerCase()),
    );
  function recordGrid(items: DomainRecord[]) {
    return (
      <div className="record-grid">
        {items.length ? (
          items.map((r) => (
            <button
              key={r.id}
              className="record panel"
              onClick={() => setDetail(r)}
            >
              <div className="record-top">
                <span className="eyebrow">{r.domain}</span>
                <ArrowUpRight size={16} />
              </div>
              <h3>{r.title}</h3>
              <div className="record-value">
                {r.value} <small>{r.unit}</small>
              </div>
              <Tag
                tone={
                  /Review|Pending|Due|Stale|Expired/.test(r.status)
                    ? "amber"
                    : "neutral"
                }
              >
                {r.status}
              </Tag>
              <p>{r.method}</p>
              <footer>
                {stamp(r.measured_at)} · SIMULATED
                <br />
                Source: {r.source} ·{" "}
                {r.status === "Stale" ? "STALE" : "Simulation snapshot"}
              </footer>
            </button>
          ))
        ) : (
          <div className="empty panel">
            No matching records. Missing data is not a normal result.
          </div>
        )}
      </div>
    );
  }
  function alertList(items: Alert[]) {
    return (
      <div className="alert-list">
        {items.length ? (
          items.map((a) => (
            <button
              className="alert-row"
              key={a.id}
              onClick={() => setDetail(a)}
            >
              <span className={`severity ${a.severity}`}>
                <Bell size={16} />
              </span>
              <span>
                <b>{a.title}</b>
                <small>
                  {state.crew.find((c) => c.id === a.astronaut_id)
                    ?.display_name || "Habitat · shared environment"}{" "}
                  · {a.rule_id} v{a.rule_version}
                </small>
              </span>
              <Tag tone={a.status === "open" ? "amber" : "neutral"}>
                {a.status === "open" ? a.severity : a.status}
              </Tag>
              <ChevronRight size={16} />
            </button>
          ))
        ) : (
          <div className="empty">
            <Shield size={24} />
            <h3>No open demo alerts</h3>
            <p>Run a mission scenario to inspect an alarm and its evidence.</p>
          </div>
        )}
      </div>
    );
  }
  return (
    <div className="app">
      <a className="skip" href="#main">
        Skip to dashboard
      </a>
      <aside className={menu ? "sidebar show" : "sidebar"}>
        <div className="brand">
          <div className="brand-mark">
            <Orbit size={26} />
          </div>
          <div>
            TEAMROCKET<small>FLIGHT HEALTH SYSTEMS</small>
          </div>
        </div>
        <div className="mission-chip">
          <span className="status-dot" />
          <div>
            DEMO-01 · Deep space<small>Transit phase / Mission day 46</small>
          </div>
        </div>
        <nav>
          {nav.map(
            (n, i) =>
              canAccess(state.role, n.id) && (
                <div key={n.id}>
                  {(i === 0 || nav[i - 1].group !== n.group) && (
                    <p className="nav-group">{n.group}</p>
                  )}
                  <button
                    className={view === n.id ? "nav-item active" : "nav-item"}
                    onClick={() => go(n.id)}
                  >
                    <n.icon size={18} />
                    {n.label}
                    {view === n.id && <span className="active-dot" />}
                  </button>
                </div>
              ),
          )}
        </nav>
        <div className="sidebar-bottom">
          <div className="orbit-art">
            <Orbit size={50} />
          </div>
          <strong>Built for the journey.</strong>
          <p>
            NASA Space Apps Challenge
            <br />
            Independent research prototype
          </p>
          <Tag>SIMULATED DATA ONLY</Tag>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <button
            className="mobile-menu icon-button"
            aria-label="Open navigation"
            onClick={() => setMenu(!menu)}
          >
            <Menu />
          </button>
          <div className="breadcrumb">
            Flight health <ChevronRight size={14} />{" "}
            <b>{nav.find((n) => n.id === view)?.label}</b>
          </div>
          <div className="top-actions">
            <span className="connection">
              {offline ? <WifiOff size={15} /> : <Wifi size={15} />}{" "}
              {isMock
                ? offline
                  ? "Demo offline"
                  : "Demo connected"
                : "API mode"}
            </span>
            <button
              className="icon-button"
              title="Enable or disable alarm audio"
              aria-label={sound ? "Mute alarm audio" : "Enable alarm audio"}
              onClick={() => {
                if (!audio) {
                  const a = new AudioContext();
                  a.resume();
                  setAudio(a);
                } else audio.resume();
                setSound(!sound);
              }}
            >
              {sound ? <Volume2 size={18} /> : <VolumeX size={18} />}
            </button>
            <button
              className="avatar"
              onClick={() => setIntegration(!integration)}
              aria-label="Integration and account settings"
            >
              TR
            </button>
          </div>
        </header>
        <main id="main">
          <div className="demo-banner">
            <span>
              <span className="status-dot" />{" "}
              {isMock ? "SIMULATION MODE" : "BACKEND MODE"}{" "}
              <b>
                {isMock
                  ? "Fictional crew · not clinically validated"
                  : "Authenticated API required"}
              </b>
            </span>
            <span>SIM CLOCK · {stamp(state.simulation_time)}</span>
          </div>
          {integration && (
            <section className="panel integration">
              <h3>Backend integration</h3>
              <p>
                Mock mode runs immediately. API mode uses the proposed FastAPI
                contract. Credentials remain in memory only.
              </p>
              {!isMock && (
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    setAccessToken(
                      String(new FormData(e.currentTarget).get("token")),
                    );
                    e.currentTarget.reset();
                    reload();
                  }}
                >
                  <label>
                    Supabase access token (temporary developer handoff)
                    <input
                      name="token"
                      type="password"
                      autoComplete="off"
                      required
                    />
                  </label>
                  <button className="primary">Connect API</button>
                </form>
              )}
              <code>VITE_DATA_MODE={isMock ? "mock" : "api"}</code>
            </section>
          )}
          {error && (
            <div role="alert" className="error">
              {error}
              <button onClick={() => setError("")} aria-label="Dismiss error">
                <X size={16} />
              </button>
            </div>
          )}
          {notice && (
            <div role="status" className="notice">
              <Check size={16} />
              {notice}
            </div>
          )}
          <div className="page-heading">
            <div>
              <p className="eyebrow">
                {view === "command"
                  ? "MISSION CONTROL / HEALTH OVERVIEW"
                  : "DEMO-01 / CREW HEALTH OPERATIONS"}
              </p>
              <h1>{title[view]}</h1>
              <p>{sub[view]}</p>
            </div>
            <button className="secondary" onClick={exportData}>
              <Download size={15} />
              Export snapshot
            </button>
          </div>
          <div className="toolbar">
            <div className="toolbar-left">
              {view !== "command" && (
                <label className="select-label">
                  Crew
                  <select
                    value={crew?.id}
                    onChange={(e) => setSelected(e.target.value)}
                  >
                    {s.crew.map((c) => (
                      <option value={c.id} key={c.id}>
                        {c.display_name}
                      </option>
                    ))}
                  </select>
                </label>
              )}
              {isMock && (
                <label className="select-label">
                  Demo role
                  <select
                    value={state.role}
                    onChange={(e) => role(e.target.value as Role)}
                  >
                    {[
                      "crew",
                      "crew_medical_officer",
                      "ground_clinician",
                      "mission_operator",
                      "administrator",
                    ].map((r) => (
                      <option key={r} value={r}>
                        {r.replaceAll("_", " ")}
                      </option>
                    ))}
                  </select>
                </label>
              )}
            </div>
            <label className="search">
              <Search size={16} />
              <input
                aria-label="Search records"
                placeholder="Search this workspace…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </label>
          </div>
          {loading ? (
            <div className="empty panel">Loading mission records…</div>
          ) : !apiReady && !isMock ? (
            <div className="empty panel">
              Backend data unavailable. Open account settings to connect; no
              mock data is shown in API mode.
            </div>
          ) : (
            <>
              {view === "command" && (
                <>
                  <div className="stats">
                    <div className="stat panel">
                      <span>
                        CREW ON MISSION
                        <Users size={17} />
                      </span>
                      <strong>
                        04 <small>/ 04 assigned</small>
                      </strong>
                      <footer>Fictional mission roster</footer>
                    </div>
                    <div className="stat panel">
                      <span>
                        OPEN ALERTS
                        <Bell size={17} />
                      </span>
                      <strong className={open.length ? "amber-text" : ""}>
                        {String(open.length).padStart(2, "0")}{" "}
                        <small>requiring attention</small>
                      </strong>
                      <footer>
                        {open.filter((a) => a.severity === "critical").length}{" "}
                        critical · inspect evidence below
                      </footer>
                    </div>
                    <div className="stat panel">
                      <span>
                        UPCOMING EXAMS
                        <Stethoscope size={17} />
                      </span>
                      <strong>
                        08 <small>OCT eye assessments</small>
                      </strong>
                      <footer>Due 16 June · simulation schedule</footer>
                    </div>
                    <div className="stat panel">
                      <span>
                        SYNC QUEUE
                        <Radio size={17} />
                      </span>
                      <strong>
                        {String(queued.length).padStart(2, "0")}{" "}
                        <small>pending demo events</small>
                      </strong>
                      <footer>
                        {offline
                          ? "Locally saved · waiting for reconnect"
                          : "Demo receipts · no cloud transmission"}
                      </footer>
                    </div>
                  </div>
                  <div className="section-heading">
                    <h2>
                      Crew health overview <span>4 ASTRONAUTS</span>
                    </h2>
                    <span className="muted">
                      Select a crew member to explore
                    </span>
                  </div>
                  <div className="crew-grid">
                    {s.crew
                      .filter((c) =>
                        c.display_name
                          .toLowerCase()
                          .includes(search.toLowerCase()),
                      )
                      .map((c, i) => {
                        const alerts = s.alerts.filter(
                            (a) =>
                              a.status !== "resolved" &&
                              (a.astronaut_id === c.id ||
                                a.astronaut_id === null),
                          ),
                          hr = s.measurements.find(
                            (m) =>
                              m.astronaut_id === c.id && m.metric_code === "HR",
                          );
                        return (
                          <button
                            className="crew-card panel"
                            key={c.id}
                            onClick={() => {
                              if (canAccess(state.role, "astronaut")) {
                                setSelected(c.id);
                                go("astronaut");
                              } else
                                setNotice(
                                  "Individual medical data is restricted to clinical roles.",
                                );
                            }}
                          >
                            <div className="crew-top">
                              <span className="crew-number">0{i + 1}</span>
                              <Tag tone={alerts.length ? "amber" : "mint"}>
                                {alerts.length
                                  ? `${alerts.length} attention`
                                  : "Baseline demo"}
                              </Tag>
                            </div>
                            <div
                              className="crew-emblem"
                              style={
                                {
                                  "--crew-color": c.color,
                                } as React.CSSProperties
                              }
                            >
                              <svg viewBox="0 0 120 110" aria-hidden="true">
                                <ellipse
                                  cx="60"
                                  cy="53"
                                  rx="39"
                                  ry="43"
                                  fill="currentColor"
                                  opacity=".15"
                                />
                                <rect
                                  x="25"
                                  y="44"
                                  width="70"
                                  height="53"
                                  rx="28"
                                  fill="#b8c6d2"
                                />
                                <circle cx="60" cy="38" r="29" fill="#dce6ec" />
                                <rect
                                  x="36"
                                  y="24"
                                  width="48"
                                  height="29"
                                  rx="13"
                                  fill="#182632"
                                />
                                <path
                                  d="M43 31h14"
                                  stroke="currentColor"
                                  strokeWidth="3"
                                />
                                <rect
                                  x="45"
                                  y="71"
                                  width="30"
                                  height="18"
                                  rx="4"
                                  fill="#233442"
                                />
                                <rect
                                  x="51"
                                  y="77"
                                  width="18"
                                  height="4"
                                  fill="currentColor"
                                />
                              </svg>
                            </div>
                            <h3>{c.display_name}</h3>
                            <p>
                              {c.crew_role} <span>· {c.crew_code}</span>
                            </p>
                            <div className="crew-vital">
                              <span>Heart rate</span>
                              <strong>
                                {hr ? displayValue(hr) : "Restricted"}{" "}
                                <small>{hr ? "bpm" : ""}</small>
                              </strong>
                            </div>
                            {hr && (
                              <Spark values={hr.history} color={c.color} />
                            )}
                            <footer>
                              SIMULATED ·{" "}
                              {hr
                                ? "Demo fixture · 15 Jun, 12:00 UTC"
                                : "Clinical data restricted"}
                              <ArrowUpRight size={15} />
                            </footer>
                          </button>
                        );
                      })}
                  </div>
                  <div className="bottom-grid">
                    <section className="panel">
                      <div className="panel-heading">
                        <h2>Alerts & incident watch</h2>
                        <Tag tone="mint">{open.length} OPEN</Tag>
                      </div>
                      {alertList(open)}
                    </section>
                    <section className="panel mission-panel">
                      <div className="panel-heading">
                        <h2>Mission context</h2>
                        <Orbit size={18} />
                      </div>
                      <div className="mission-orbit">
                        <Orbit size={86} />
                        <div>
                          <strong>DEMO-01</strong>
                          <p>180-day deep-space mission</p>
                        </div>
                      </div>
                      <div className="progress">
                        <i />
                      </div>
                      <div className="split muted">
                        <span>Day 46</span>
                        <span>180 simulated days</span>
                      </div>
                      <div className="hazards">
                        {[
                          "Radiation",
                          "Isolation & confinement",
                          "Distance from Earth",
                          "Altered gravity",
                          "Hostile / closed environment",
                        ].map((h, i) => (
                          <span key={h}>
                            <i>0{i + 1}</i>
                            {h}
                          </span>
                        ))}
                      </div>
                    </section>
                  </div>
                </>
              )}
              {view === "astronaut" && (
                <>
                  <div className="profile-layout">
                    <section className="panel profile">
                      <div className="panel-heading">
                        <Tag tone="mint">{crew.crew_code}</Tag>
                        <span className="muted">DEMO-01</span>
                      </div>
                      <Astronaut color={crew.color} name={crew.display_name} />
                      <h2>{crew.display_name}</h2>
                      <p>{crew.crew_role} · Transit phase</p>
                      <div className="split">
                        <Tag>SIMULATED PROFILE</Tag>
                        <span className="muted">No real medical records</span>
                      </div>
                    </section>
                    <section>
                      <div className="section-heading">
                        <h2>Vital signs</h2>
                        <select
                          aria-label="Trend window"
                          value={range}
                          onChange={(e) => setRange(e.target.value)}
                        >
                          <option value="30">30 days</option>
                          <option value="7">7 days</option>
                        </select>
                      </div>
                      <div className="metrics">
                        {myVitals.map((m) => (
                          <Metric
                            key={m.id}
                            m={{
                              ...m,
                              history: m.history.slice(-Number(range)),
                            }}
                            onClick={() => setDetail(m)}
                          />
                        ))}
                      </div>
                    </section>
                  </div>
                  <section className="panel">
                    <div className="panel-heading">
                      <h2>Personal alert timeline</h2>
                      <Tag>Evidence linked</Tag>
                    </div>
                    {alertList(
                      s.alerts.filter(
                        (a) =>
                          a.astronaut_id === crew.id || a.astronaut_id === null,
                      ),
                    )}
                  </section>
                  <div className="section-heading">
                    <h2>Daily health & baselines</h2>
                  </div>
                  {recordGrid(
                    filtered([
                      "Cardiorespiratory",
                      "Sleep / behavior",
                      "Fitness / muscle",
                      "Nutrition / fluids",
                      "Gravity / vestibular",
                    ]),
                  )}
                  <section className="panel">
                    <div className="panel-heading">
                      <h2>Reported symptoms & personal history</h2>
                    </div>
                    {s.events
                      .filter(
                        (e) =>
                          e.payload.astronaut_id === crew.id &&
                          e.entity_type === "symptom_reports",
                      )
                      .map((e) => (
                        <div className="timeline" key={e.event_id}>
                          <Tag>{e.status}</Tag>
                          <b>{String(e.payload.symptom_code)}</b>
                          <span>
                            {String(e.payload.severity)} ·{" "}
                            {stamp(e.occurred_at)}
                          </span>
                        </div>
                      ))}
                    {!s.events.some(
                      (e) =>
                        e.entity_type === "symptom_reports" &&
                        e.payload.astronaut_id === crew.id,
                    ) && (
                      <p className="empty">
                        No symptom reports in this demo session.
                      </p>
                    )}
                  </section>
                </>
              )}
              {view === "exams" && (
                <>
                  <div className="info-strip">
                    <Stethoscope size={20} />
                    <span>
                      Compare only matching eye, side, region, and method.
                      In-flight DXA remains unavailable.
                    </span>
                  </div>
                  {recordGrid(
                    filtered([
                      "Vascular",
                      "Vision / SANS",
                      "Bone",
                      "Fitness / muscle",
                      "Gravity / vestibular",
                    ]),
                  )}
                </>
              )}
              {view === "environment" && (
                <>
                  <div className="info-strip">
                    <Radiation size={20} />
                    <span>
                      Dose equivalent (mSv) and absorbed dose (mGy) are separate
                      quantities. No automatic conversion or shielding estimate.
                    </span>
                  </div>
                  {recordGrid(
                    filtered([
                      "Radiation",
                      "Cabin environment",
                      "Environmental microbiology",
                    ]),
                  )}
                </>
              )}
              {view === "laboratory" && (
                <>
                  <div className="info-strip">
                    <FlaskConical size={20} />
                    <span>
                      Assay method, sample custody, verification, and analyst
                      review travel with every result. No inferred immune score.
                    </span>
                  </div>
                  {recordGrid(
                    filtered(["Immune / infection", "Vascular"]).filter(
                      (r) => r.table !== "vascular_ultrasound_results",
                    ),
                  )}
                </>
              )}
              {view === "self" && (
                <>
                  <div className="forms-grid">
                    <form className="panel form-panel" onSubmit={report}>
                      <Tag tone="mint">CREW REPORT</Tag>
                      <h2>How are you feeling?</h2>
                      <p>
                        Reports are linked to {crew.display_name}. Severe
                        symptoms trigger a demo incident even if sensor data is
                        missing.
                      </p>
                      <label>
                        Symptom
                        <select name="symptom" required>
                          <option value="breathing_difficulty">
                            Breathing difficulty
                          </option>
                          <option value="headache">Headache</option>
                          <option value="chest_pain">Chest pain</option>
                          <option value="vision_loss">
                            Sudden visual change
                          </option>
                          <option value="dizziness">Dizziness</option>
                          <option value="nausea">Nausea</option>
                          <option value="fatigue">Fatigue</option>
                          <option value="other">Other</option>
                        </select>
                      </label>
                      <label>
                        Severity
                        <select name="severity">
                          <option value="mild">Mild</option>
                          <option value="moderate">Moderate</option>
                          <option value="severe">
                            Severe — medical attention requested
                          </option>
                        </select>
                      </label>
                      <label>
                        Onset time (UTC)
                        <input
                          type="datetime-local"
                          name="onset"
                          defaultValue="2026-06-15T12:00"
                          required
                        />
                      </label>
                      <label>
                        Context / notes
                        <textarea
                          name="notes"
                          maxLength={1000}
                          placeholder="Activity, duration, and relevant context"
                        />
                      </label>
                      <button className="primary" disabled={busy}>
                        {busy ? "Saving…" : "Submit symptom report"}
                        <ChevronRight size={16} />
                      </button>
                    </form>
                    <form className="panel form-panel" onSubmit={checkin}>
                      <Tag>CONFIDENTIAL DEMO CHECK-IN</Tag>
                      <h2>A moment to check in.</h2>
                      <p>
                        This panel is restricted to crew and medical roles in
                        the demo. Backend authorization and RLS must enforce
                        confidentiality in production.
                      </p>
                      <label>
                        Fatigue (0–10)
                        <input
                          name="fatigue"
                          type="number"
                          min="0"
                          max="10"
                          defaultValue="3"
                          required
                        />
                      </label>
                      <label>
                        Private notes
                        <textarea
                          name="private"
                          maxLength={1000}
                          placeholder="Use fictional data only in this prototype."
                        />
                      </label>
                      <button className="secondary" disabled={!isMock}>
                        Save private demo check-in
                      </button>
                      {!isMock && (
                        <p>
                          Private-check-in write endpoint awaits backend
                          implementation.
                        </p>
                      )}
                      <div className="guidance">
                        <Shield size={22} />
                        <p>
                          No autonomous diagnosis, prescription, or EVA
                          clearance. Report urgent concerns to the responsible
                          medical team.
                        </p>
                      </div>
                    </form>
                  </div>
                  <div className="section-heading">
                    <h2>Adaptation & personal reminders</h2>
                  </div>
                  {recordGrid(
                    filtered([
                      "Gravity / vestibular",
                      "Vision / SANS",
                      "Autonomous medical",
                    ]),
                  )}
                </>
              )}
              {view === "ground" && (
                <>
                  <div className="stats">
                    <div className="stat panel">
                      <span>RECEIVED DEMO EVENTS</span>
                      <strong>
                        {s.events.filter((e) => e.status === "received").length}
                      </strong>
                    </div>
                    <div className="stat panel">
                      <span>QUEUED EVENTS</span>
                      <strong>{queued.length}</strong>
                    </div>
                    <div className="stat panel">
                      <span>COMMUNICATION DELAY</span>
                      <strong>
                        20 <small>min · demo context</small>
                      </strong>
                    </div>
                    <div className="stat panel">
                      <span>REVIEW REQUIRED</span>
                      <strong>
                        {
                          records.filter((r) => /Pending|Review/.test(r.status))
                            .length
                        }
                      </strong>
                    </div>
                  </div>
                  <section className="panel">
                    <div className="panel-heading">
                      <h2>Incident & acknowledgment timeline</h2>
                    </div>
                    {alertList(s.alerts)}
                  </section>
                  <div className="section-heading">
                    <h2>Clinical review queue</h2>
                  </div>
                  {recordGrid(
                    records.filter((r) => /Pending|Review/.test(r.status)),
                  )}
                  <section className="panel">
                    <div className="panel-heading">
                      <h2>Append-only demo event history</h2>
                      <Tag>{s.events.length} EVENTS</Tag>
                    </div>
                    {s.events.length ? (
                      s.events.map((e) => (
                        <div className="timeline" key={e.event_id}>
                          <Tag tone={e.status === "queued" ? "amber" : "mint"}>
                            {e.status}
                          </Tag>
                          <div>
                            <b>{e.entity_type.replaceAll("_", " ")}</b>
                            <small>
                              {stamp(e.occurred_at)} · {e.event_id}
                            </small>
                            <p>
                              {e.entity_type === "behavioral_checkins"
                                ? "Confidential content omitted from general audit"
                                : JSON.stringify(e.payload)}
                            </p>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="empty">
                        Run a scenario or submit a report to populate the
                        timeline.
                      </div>
                    )}
                  </section>
                </>
              )}
              {view === "operations" && (
                <>
                  <div className="info-strip">
                    <Shield size={20} />
                    <span>
                      Demo-approved guidance only. Expired or unapproved
                      versions cannot be acknowledged as operational guidance.
                    </span>
                  </div>
                  {recordGrid(filtered(["Autonomous medical"]))}
                  <section className="panel form-panel">
                    <h2>Condition reference catalog</h2>
                    <p>
                      20 synthetic catalog entries are specified for backend
                      seeding. IMM 100 / CLiFF 119 source content is not
                      supplied. No claim of complete official catalog coverage.
                    </p>
                    <Tag tone="amber">AUTHORITATIVE CATALOG IMPORT PENDING</Tag>
                    <h3>Decision-node contract</h3>
                    <p>
                      Procedure ID/version → approved branch criterion →
                      clinician escalation → authorized inventory availability
                      and expiry. MORD is a source reference, not an executable
                      treatment tree.
                    </p>
                  </section>
                </>
              )}
              {view === "research" && (
                <>
                  <div className="record-grid">
                    {["CHI", "TME", "QTL", "EVAC", "LOCL"].map((n) => (
                      <article className="panel record" key={n}>
                        <Tag tone="amber">NOT VALIDATED</Tag>
                        <h2>{n}</h2>
                        <p>
                          Source-controlled formula not provided. Calculation
                          disabled.
                        </p>
                        <footer>
                          Required: version, source, input availability,
                          calculation provenance, reviewer, mission
                          applicability.
                        </footer>
                      </article>
                    ))}
                  </div>
                  <section className="panel form-panel">
                    <h2>Source & approval register</h2>
                    <p>
                      NASA-STD-3001 Volumes 1–2, NASA HRP risk articles, NASA
                      medical technical briefs, and CSA Bio-Monitor,
                      Bio-Analyzer and ACTIS descriptions are source candidates
                      from the PDF. Current revisions and applicable limits must
                      be verified by your research reviewer.
                    </p>
                    <p>
                      Each active rule needs document title, URL, revision/date,
                      page, reviewer, applicability, approval state, and a test
                      case. No clinical limit is assumed by this frontend.
                    </p>
                  </section>
                </>
              )}
              {view === "data" && (
                <>
                  <div className="stats">
                    {[
                      ["57", "CLOUD TABLES"],
                      ["06", "SQLITE TABLES"],
                      ["47", "FEATURES"],
                      ["12", "SCENARIOS"],
                    ].map(([n, l]) => (
                      <div className="stat panel" key={l}>
                        <span>{l}</span>
                        <strong>{n}</strong>
                        <footer>
                          MasterDocs scope · not backend completion
                        </footer>
                      </div>
                    ))}
                  </div>
                  <section className="panel data-table">
                    <div className="panel-heading">
                      <h2>Canonical cloud table inventory</h2>
                      <Tag>PDF · pp. 3–5</Tag>
                    </div>
                    <table>
                      <thead>
                        <tr>
                          <th>Table</th>
                          <th>Required starter fields</th>
                          <th>Integration state</th>
                        </tr>
                      </thead>
                      <tbody>
                        {catalog.tables
                          .filter((t) =>
                            `${t.name} ${t.fields.join(" ")}`.includes(
                              search.toLowerCase(),
                            ),
                          )
                          .map((t) => (
                            <tr key={t.name}>
                              <td>
                                <code>{t.name}</code>
                              </td>
                              <td>{t.fields.join(", ")}</td>
                              <td>
                                <Tag>Backend pending</Tag>
                              </td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </section>
                  <section className="panel data-table">
                    <div className="panel-heading">
                      <h2>Feature scope</h2>
                    </div>
                    <table>
                      <thead>
                        <tr>
                          <th>ID</th>
                          <th>Requirement</th>
                          <th>Phase</th>
                        </tr>
                      </thead>
                      <tbody>
                        {catalog.features
                          .filter((f) =>
                            `${f.id} ${f.name}`
                              .toLowerCase()
                              .includes(search.toLowerCase()),
                          )
                          .map((f) => (
                            <tr key={f.id}>
                              <td>{f.id}</td>
                              <td>{f.name}</td>
                              <td>{f.phase}</td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </section>
                  <div className="info-strip">
                    Offline tables: offline_vital_signs,
                    offline_symptom_reports, offline_health_alerts,
                    offline_alert_rules, offline_medical_procedures, sync_queue.
                    SQLite belongs to FastAPI; this browser demo uses
                    localStorage for fictional data only.
                  </div>
                </>
              )}
            </>
          )}
          {isMock && (
            <section className="scenario-bar">
              <div>
                <strong>
                  <Activity size={16} /> Mission simulator
                </strong>
                <small>Versioned demo fixtures · no clinical thresholds</small>
              </div>
              <select
                aria-label="Mission scenario"
                value={scenario}
                onChange={(e) => setScenario(e.target.value)}
              >
                {scenarios.map(([id, label]) => (
                  <option value={id} key={id}>
                    {id} · {label}
                  </option>
                ))}
              </select>
              <button className="primary" onClick={run}>
                Run scenario
                <ChevronRight size={15} />
              </button>
              <button
                className="secondary"
                onClick={() => (offline ? reconnect() : setOffline(true))}
              >
                {offline ? "Reconnect demo" : "Disconnect demo"}
              </button>
              <button
                className="icon-button"
                title="Reset fictional demo"
                aria-label="Reset demo"
                onClick={() => {
                  setState(initialSnapshot());
                  setOffline(false);
                  setView("command");
                  setNotice("Fictional demo reset.");
                }}
              >
                <RotateCcw size={17} />
              </button>
            </section>
          )}
          <footer className="page-footer">
            <span>TEAMROCKET / NASA SPACE APPS CHALLENGE</span>
            <span>
              Independent prototype · {isMock ? "SIMULATED" : "API"} · No flight
              medical certification
            </span>
          </footer>
        </main>
      </div>
      {detail && (
        <div className="modal-backdrop" onClick={() => setDetail(null)}>
          <section
            className="modal panel"
            role="dialog"
            aria-modal="true"
            aria-label="Record evidence"
            onClick={(e) => e.stopPropagation()}
            onKeyDown={(e) => {
              if (e.key === "Escape") setDetail(null);
              if (e.key === "Tab") {
                const nodes = e.currentTarget.querySelectorAll<HTMLElement>(
                  "button:not(:disabled),input,textarea,select",
                );
                const first = nodes[0],
                  last = nodes[nodes.length - 1];
                if (e.shiftKey && document.activeElement === first) {
                  e.preventDefault();
                  last.focus();
                } else if (!e.shiftKey && document.activeElement === last) {
                  e.preventDefault();
                  first.focus();
                }
              }
            }}
          >
            <button
              autoFocus
              className="modal-close icon-button"
              onClick={() => setDetail(null)}
              aria-label="Close record"
            >
              <X />
            </button>
            <Tag tone="mint">
              {detail.is_synthetic ? "SIMULATED RECORD" : "API RECORD"}
            </Tag>
            <h2>{"title" in detail ? detail.title : detail.metric_code}</h2>
            <p className="muted">Immutable evidence and provenance</p>
            <dl>
              {Object.entries(detail)
                .filter(([k]) => k !== "history")
                .map(([k, v]) => (
                  <div key={k}>
                    <dt>{k.replaceAll("_", " ")}</dt>
                    <dd>
                      {v === null
                        ? "Unavailable"
                        : typeof v === "object"
                          ? JSON.stringify(v, null, 2)
                          : String(v)}
                    </dd>
                  </div>
                ))}
            </dl>
            {"severity" in detail &&
              detail.status === "open" &&
              [
                "crew_medical_officer",
                "ground_clinician",
                "administrator",
              ].includes(state.role) && (
                <button
                  className="primary"
                  disabled={busy}
                  onClick={() => ack(detail)}
                >
                  Acknowledge alert
                </button>
              )}
            {"table" in detail &&
              [
                "crew_medical_officer",
                "ground_clinician",
                "administrator",
              ].includes(state.role) && (
                <form
                  className="review-form"
                  onSubmit={async (e) => {
                    e.preventDefault();
                    const note = String(
                      new FormData(e.currentTarget).get("note"),
                    );
                    setBusy(true);
                    try {
                      const ev = event(
                        "clinical_review",
                        {
                          record_id: detail.id,
                          note,
                          astronaut_id: detail.astronaut_id,
                        },
                        offline,
                      );
                      await sendReview(detail.id, note, ev.event_id);
                      setState((old) => ({
                        ...old,
                        records: old.records.map((r) =>
                          r.id === detail.id
                            ? { ...r, status: "Demo review recorded" }
                            : r,
                        ),
                        events: [ev, ...old.events],
                      }));
                      setDetail(null);
                      if (!isMock) await reload();
                      setNotice(
                        "Review recorded; no diagnosis or treatment generated.",
                      );
                    } catch (e) {
                      setError((e as Error).message);
                    } finally {
                      setBusy(false);
                    }
                  }}
                >
                  <label>
                    Review note
                    <textarea name="note" required maxLength={1000} />
                  </label>
                  <button className="primary" disabled={busy}>
                    Record review
                  </button>
                </form>
              )}
            {"table" in detail && detail.table === "medical_procedures" && (
              <button
                className="secondary"
                disabled={
                  detail.details.approval_status !== "approved_for_demo" ||
                  !isMock
                }
                onClick={() => {
                  setState((old) => ({
                    ...old,
                    events: [
                      event(
                        "procedure_acknowledgment",
                        {
                          procedure_id: detail.id,
                          version: 1,
                          astronaut_id: crew.id,
                        },
                        offline,
                      ),
                      ...old.events,
                    ],
                  }));
                  setNotice("Demo procedure acknowledgment saved.");
                  setDetail(null);
                }}
              >
                Acknowledge demo guidance
              </button>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
