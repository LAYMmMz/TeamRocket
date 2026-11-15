"""TeamRocket: development-only, automatic SQLite team-schema projection.

Source of truth: app.offline.store.Store (encrypted offline.db).
Destination: teammate's separate data/astronaut_health.db.
This is a non-transactional, idempotent projection. NO cloud sync is performed.
Only synthetic source records are copied to the plaintext teammate database.

Usage from Developer1_Backend/backend:
    python team_sqlite_integration.py DEMO-02
    python team_sqlite_integration.py --all
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import sqlite3
import sys

from team_sqlite import DB_PATH, get_db

log = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent
VITAL_METRICS = {
    "heart_rate", "spo2", "respiratory_rate", "systolic_bp",
    "diastolic_bp", "temperature",
}
ENVIRONMENT_METRICS = {"ppco2", "ppo2", "pressure", "noise", "light"}
QUALITY = {
    "VALID": "Valid", "SUSPECT": "Suspect", "INVALID": "Invalid",
    "MISSING": "Unknown", "STALE": "Unknown",
}
# These are display equivalences, not clinical thresholds.
SEVERITY = {"information": "Info", "warning": "Warning", "critical": "Critical"}
KINDS = ("measurement", "symptom_report", "health_alert", "alert_rule", "procedure")
REQUIRED_TABLES = {
    "vital_signs", "symptom_reports", "health_alerts", "alert_rules",
    "medical_procedures", "radiation_readings", "environmental_readings",
    "sync_outbox",
}

class NotMappable(Exception):
    """A valid source record cannot be represented faithfully in team schema."""


def integration_ready():
    """Used by FastAPI startup; never creates a missing database."""
    return DB_PATH.is_file() and (ROOT / "team_sqlite.py").is_file()


def require_synthetic(record):
    if record.get("is_synthetic") is not True or record.get("source_type") != "SIMULATED":
        raise NotMappable("not_simulated")


def need(record, *keys):
    for key in keys:
        if record.get(key) is None or record.get(key) == "":
            raise NotMappable("required_field_missing")


def columns_for(kind, record):
    """Return (destination_table, row_dict) without deriving clinical values."""
    if not isinstance(record, dict):
        raise NotMappable("invalid_payload")

    if kind == "measurement":
        require_synthetic(record)
        need(record, "event_id", "mission_id", "measured_at", "received_at", "metric", "unit")
        metric = record["metric"]
        quality = QUALITY.get(record.get("quality"))
        if quality is None:
            raise NotMappable("quality_not_mappable")
        value = record.get("value")
        if value is None:  # teammate tables require non-null real values
            raise NotMappable("missing_measurement_value")
        common = dict(
            id=record["event_id"], mission_id=record["mission_id"],
            original_value=value, original_unit=record["unit"],
            quality_status=quality, measured_at=record["measured_at"],
            received_at=record["received_at"],
        )
        if metric in VITAL_METRICS:
            need(record, "astronaut_id")
            return "vital_signs", dict(
                common, astronaut_id=record["astronaut_id"],
                source_device_id=record.get("device_id"),
                source_type="SIMULATED", metric_code=metric,
                normalized_value=record.get("normalized_value"),
                normalized_unit=record.get("normalized_unit"),
            )
        if metric == "radiation_dose":
            need(record, "astronaut_id")
            dose_type = (record.get("metadata") or {}).get("dose_type")
            if dose_type not in ("rate", "cumulative"):
                # Do not guess a cumulative/rate classification from units.
                raise NotMappable("radiation_dose_type_missing")
            return "radiation_readings", dict(
                common, astronaut_id=record["astronaut_id"],
                dosimeter_id=record.get("device_id"), dose_type=dose_type,
            )
        if metric in ENVIRONMENT_METRICS:
            compartment = (record.get("metadata") or {}).get("zone")
            if not isinstance(compartment, str) or not compartment.strip():
                raise NotMappable("environment_zone_missing")
            return "environmental_readings", dict(
                common, compartment_name=compartment,
                parameter_name=metric,
            )
        raise NotMappable("metric_has_no_team_table")

    if kind == "health_alert":
        require_synthetic(record)
        need(record, "event_id", "mission_id", "evidence_event_id", "received_at")
        need(record, "astronaut_id")  # team schema requires astronaut_id
        severity = SEVERITY.get(record.get("severity"))
        if severity is None:
            raise NotMappable("alert_severity_not_mappable")
        source = record.get("evidence_snapshot") or {}
        if source.get("symptom") is not None:
            source_table = "symptom_reports"
        elif source.get("metric") in VITAL_METRICS:
            source_table = "vital_signs"
        elif source.get("metric") == "radiation_dose":
            source_table = "radiation_readings"
        elif source.get("metric") in ENVIRONMENT_METRICS:
            source_table = "environmental_readings"
        else:
            source_table = "unmapped_evidence"
        return "health_alerts", dict(
            id=record["event_id"], astronaut_id=record["astronaut_id"],
            mission_id=record["mission_id"], rule_id=None,
            source_record_id=record["evidence_event_id"], source_table=source_table,
            severity=severity, title=record.get("message") or record.get("label") or "SIMULATED ALERT",
            evidence_json=json.dumps(source, sort_keys=True, separators=(",", ":")),
            status="Active", acknowledged_by=None, acknowledged_at=None,
            triggered_at=record["received_at"],
        )

    if kind == "procedure":
        require_synthetic(record)
        if record.get("mode") != "DEMO":
            raise NotMappable("not_demo_procedure")
        need(record, "procedure_id", "version", "title")
        steps = record.get("steps")
        if not isinstance(steps, list) or not steps:
            raise NotMappable("procedure_steps_missing")
        version = int(record["version"])
        # Teammate schema has UNIQUE procedure_code; keep each version distinct.
        return "medical_procedures", dict(
            id=f"{record['procedure_id']}:v{version}",
            procedure_code=f"{record['procedure_id']}-v{version}",
            title=record["title"], category="SIMULATED_DEMO",
            steps_json=json.dumps(steps, sort_keys=True, separators=(",", ":")),
            approved_by=None, version=version,
            updated_at=record.get("valid_from") or datetime.now(timezone.utc).isoformat(),
        )

    if kind == "symptom_report":
        # Backend classifies severity as serious/severe/critical; teammate DB
        # requires an integer 1..10. Mapping would invent clinical severity.
        raise NotMappable("symptom_severity_scale_incompatible")

    if kind == "alert_rule":
        # Rule modes/approval windows and severity classifications are not
        # faithfully represented by teammate's simplified alert_rules schema.
        raise NotMappable("rule_approval_contract_incompatible")

    raise NotMappable("unknown_kind")


def _validate_schema(db):
    names = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    missing = REQUIRED_TABLES - names
    if missing:
        raise RuntimeError("Teammate SQLite schema incomplete: " + ", ".join(sorted(missing)))


def _insert_if_absent(db, table, row):
    cols = tuple(row)
    existing = db.execute(
        "SELECT " + ",".join(cols) + " FROM " + table + " WHERE id=?",
        (row["id"],),
    ).fetchone()
    if existing is not None:
        return "already_present" if dict(existing) == row else "conflict"
    try:
        db.execute(
            f"INSERT INTO {table} (" + ",".join(cols) + ") VALUES ("
            + ",".join("?" for _ in cols) + ")",
            tuple(row[c] for c in cols),
        )
    except sqlite3.IntegrityError:
        return "conflict"  # never replace earlier evidence
    return "copied"


def reconcile(store, mission_id=None):
    """Reconcile all supported source records into teammate SQLite.

    Idempotent; never writes to original Store, never touches either cloud queue.
    Returns aggregate counts; no health information or tokens in the report.
    """
    if not integration_ready():
        raise FileNotFoundError("team_sqlite.py or teammate data/astronaut_health.db missing")
    summary = Counter()
    detail = {}
    with get_db() as db:
        _validate_schema(db)
        for kind in KINDS:
            results = Counter()
            for record in store.list(kind, mission_id=mission_id):
                try:
                    table, row = columns_for(kind, record)
                    result = _insert_if_absent(db, table, row)
                except NotMappable as exc:
                    result = "skipped"
                    results["reason:" + str(exc)] += 1
                except (KeyError, ValueError, TypeError, sqlite3.DatabaseError) as exc:
                    log.warning("Projection error for %s: %s", kind, type(exc).__name__)
                    result = "error"
                results[result] += 1
                summary[result] += 1
            detail[kind] = dict(results)
    return {"mission": mission_id or "ALL", "total": dict(summary), "by_kind": detail}


def _load_dev_env():
    env = ROOT / ".env"
    if not env.is_file():
        raise FileNotFoundError("Missing backend/.env. Start with python dev.py")
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            name, val = line.split("=", 1)
            os.environ.setdefault(name.strip(), val.strip())


def main(args):
    if len(args) != 1 or not args[0].strip():
        print("Usage: python team_sqlite_integration.py DEMO-02  (or --all)")
        return 2
    os.chdir(ROOT)
    _load_dev_env()
    from app.core.config import Settings
    from app.offline.store import Store
    settings = Settings()
    if settings.environment != "development":
        print("Refusing: projection into plaintext SQLite is development-only")
        return 2
    if not Path(settings.sqlite_path).is_file():
        print("Missing original backend offline.db; refusing to create a new one")
        return 2
    store = Store(settings)
    try:
        stats = reconcile(store, None if args[0] == "--all" else args[0])
    finally:
        store.close()
    print(json.dumps(stats, indent=2))
    return 1 if stats["total"].get("error") or stats["total"].get("conflict") else 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as exc:
        print(f"Integration failed: {type(exc).__name__}: {exc}")
        sys.exit(1)
