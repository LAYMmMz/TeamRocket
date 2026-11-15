"""TeamRocket development-only SQLite bridge.

Copies only simulated physiological vital-sign records from the existing
FastAPI measurement store into the teammate's separate astronaut_health.db.
The existing encrypted offline.db remains authoritative.

For existing records, from Developer1_Backend/backend run:
    python team_sqlite_bridge.py DEMO-02

New records can be mirrored by calling mirror_record() after ingest(),
using the companion measurements/router.py update.

IMPORTANT: the teammate's SQLite schema stores these rows in plaintext.
Do not use this bridge for real patient/astronaut data or in production.
"""

import os
import sys
from pathlib import Path

from team_sqlite import DB_PATH, get_db

BACKEND_DIR = Path(__file__).resolve().parent

# Not every measurement is a vital sign: do not put radiation/environment
# records into the vital_signs table.
VITAL_METRICS = {
    "heart_rate", "spo2", "respiratory_rate",
    "systolic_bp", "diastolic_bp", "temperature",
}
QUALITY_MAP = {
    "VALID": "Valid",
    "SUSPECT": "Suspect",
    "INVALID": "Invalid",
    "MISSING": "Unknown",
    "STALE": "Unknown",
}
COLUMNS = (
    "id", "astronaut_id", "mission_id", "source_device_id",
    "source_type", "metric_code", "original_value", "original_unit",
    "normalized_value", "normalized_unit", "quality_status",
    "measured_at", "received_at",
)


def to_team_row(record):
    """Return a row compatible with the teammate's 8-table schema, or None."""
    if record.get("is_synthetic") is not True:
        return None
    if record.get("source_type") != "SIMULATED":
        return None
    if record.get("metric") not in VITAL_METRICS:
        return None
    if record.get("value") is None or not record.get("astronaut_id"):
        return None
    if not all(record.get(k) for k in (
        "event_id", "mission_id", "measured_at", "received_at", "unit"
    )):
        return None
    if record.get("quality") not in QUALITY_MAP:
        return None

    return {
        "id": record["event_id"],
        "astronaut_id": record["astronaut_id"],
        "mission_id": record["mission_id"],
        "source_device_id": record.get("device_id"),
        "source_type": "SIMULATED",  # Keep simulation provenance.
        "metric_code": record["metric"],
        "original_value": record["value"],
        "original_unit": record["unit"],
        "normalized_value": record.get("normalized_value"),
        "normalized_unit": record.get("normalized_unit"),
        "quality_status": QUALITY_MAP[record["quality"]],
        "measured_at": record["measured_at"],
        "received_at": record["received_at"],
    }


def mirror_record(record):
    """Idempotently mirror one validated, already-persisted record.

    Returns copied, already_present, skipped, or conflict.
    A conflict is never overwritten.
    """
    row = to_team_row(record)
    if row is None:
        return "skipped"
    if not DB_PATH.is_file():
        raise FileNotFoundError(f"Teammate SQLite database not found: {DB_PATH}")

    with get_db() as db:
        existing = db.execute(
            "SELECT " + ", ".join(COLUMNS) + " FROM vital_signs WHERE id = ?",
            (row["id"],),
        ).fetchone()
        if existing is not None:
            return "already_present" if dict(existing) == row else "conflict"

        db.execute(
            "INSERT INTO vital_signs (" + ", ".join(COLUMNS) + ") "
            "VALUES (" + ", ".join("?" for _ in COLUMNS) + ")",
            tuple(row[column] for column in COLUMNS),
        )
        return "copied"


def load_dev_env():
    """Load the same backend/.env used by dev.py, without extra packages."""
    env_file = BACKEND_DIR / ".env"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                name, value = line.split("=", 1)
                os.environ.setdefault(name.strip(), value.strip())


def mirror_existing_mission(mission_id):
    """Backfill records already written by the original FastAPI backend."""
    os.chdir(BACKEND_DIR)
    load_dev_env()
    from app.core.config import Settings
    from app.offline.store import Store

    settings = Settings()
    if settings.environment != "development":
        raise RuntimeError("Plaintext SQLite mirroring is development-only")
    if not DB_PATH.is_file():
        raise FileNotFoundError(f"Teammate SQLite database not found: {DB_PATH}")
    if not Path(settings.sqlite_path).is_file():
        raise FileNotFoundError(f"Backend offline.db not found: {settings.sqlite_path}")

    store = Store(settings)
    try:
        records = store.list("measurement", mission_id=mission_id)
    finally:
        store.close()

    stats = {key: 0 for key in (
        "copied", "already_present", "skipped", "conflict"
    )}
    for record in records:
        if record.get("mission_id") != mission_id:
            stats["skipped"] += 1
            continue
        outcome = mirror_record(record)
        stats[outcome] += 1

    print(f"Mission: {mission_id}")
    for key, count in stats.items():
        print(f"{key}: {count}")
    print("Original offline.db, audit history, and cloud queue: unchanged")
    return stats["conflict"] == 0


if __name__ == "__main__":
    if len(sys.argv) != 2 or not sys.argv[1].strip():
        print("Usage: python team_sqlite_bridge.py DEMO-02")
        sys.exit(2)
    try:
        ok = mirror_existing_mission(sys.argv[1].strip())
    except Exception as exc:
        print(f"Bridge failed: {type(exc).__name__}: {exc}")
        sys.exit(1)
    sys.exit(0 if ok else 1)
