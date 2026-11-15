import sqlite3
from pathlib import Path
from contextlib import contextmanager

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "astronaut_health.db"


@contextmanager
def get_db():
    connection = sqlite3.connect(DB_PATH, timeout=5)
    connection.row_factory = sqlite3.Row

    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")

        yield connection
        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def initialize_database():
    with get_db() as db:
        db.execute("PRAGMA journal_mode = WAL")

        db.executescript("""
            -- 1. Vital Signs (Section 4.1 Observation Standard)
            CREATE TABLE IF NOT EXISTS vital_signs (
                id TEXT PRIMARY KEY,
                astronaut_id TEXT NOT NULL,
                mission_id TEXT NOT NULL,
                source_device_id TEXT,
                source_type TEXT NOT NULL DEFAULT 'Automated Telemetry',
                metric_code TEXT NOT NULL, -- e.g., 'heart_rate', 'spo2', 'bp_sys', 'bp_dia', 'resp_rate'
                original_value REAL NOT NULL,
                original_unit TEXT NOT NULL,
                normalized_value REAL,
                normalized_unit TEXT,
                quality_status TEXT NOT NULL DEFAULT 'Valid' CHECK (quality_status IN ('Valid', 'Suspect', 'Invalid', 'Unknown')),
                measured_at TEXT NOT NULL,
                received_at TEXT NOT NULL
            );

            -- 2. Crew Symptom Reports (Offline Crew Logging)
            CREATE TABLE IF NOT EXISTS symptom_reports (
                id TEXT PRIMARY KEY,
                astronaut_id TEXT NOT NULL,
                mission_id TEXT NOT NULL,
                symptom_code TEXT NOT NULL, -- e.g., 'nausea', 'headache', 'fatigue', 'visual_disturbance'
                severity INTEGER NOT NULL CHECK (severity BETWEEN 1 AND 10),
                notes TEXT,
                measured_at TEXT NOT NULL,
                received_at TEXT NOT NULL
            );

            -- 3. Cached Approved Alert Rules (Synced Down from Ground/Supabase)
            CREATE TABLE IF NOT EXISTS alert_rules (
                id TEXT PRIMARY KEY,
                rule_code TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                metric_code TEXT NOT NULL,
                operator TEXT NOT NULL CHECK (operator IN ('>', '>=', '<', '<=', '==', '!=')),
                threshold_value REAL NOT NULL,
                unit TEXT NOT NULL,
                severity TEXT NOT NULL CHECK (severity IN ('Info', 'Warning', 'Critical')),
                procedure_id TEXT,
                is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
                updated_at TEXT NOT NULL,
                FOREIGN KEY (procedure_id) REFERENCES medical_procedures(id) ON DELETE RESTRICT
            );

            -- 4. Cached Emergency Medical Procedures (Offline Guidance)
            CREATE TABLE IF NOT EXISTS medical_procedures (
                id TEXT PRIMARY KEY,
                procedure_code TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                steps_json TEXT NOT NULL, -- JSON array of step-by-step instructions
                approved_by TEXT,
                version INTEGER NOT NULL DEFAULT 1,
                updated_at TEXT NOT NULL
            );

            -- 5. Locally Generated Health Alerts
            CREATE TABLE IF NOT EXISTS health_alerts (
                id TEXT PRIMARY KEY,
                astronaut_id TEXT NOT NULL,
                mission_id TEXT NOT NULL,
                rule_id TEXT,
                source_record_id TEXT NOT NULL,
                source_table TEXT NOT NULL,
                severity TEXT NOT NULL CHECK (severity IN ('Info', 'Warning', 'Critical')),
                title TEXT NOT NULL,
                evidence_json TEXT NOT NULL, -- JSON snapshot of triggering reading
                status TEXT NOT NULL DEFAULT 'Active' CHECK (status IN ('Active', 'Acknowledged', 'Resolved')),
                acknowledged_by TEXT,
                acknowledged_at TEXT,
                triggered_at TEXT NOT NULL,
                FOREIGN KEY (rule_id) REFERENCES alert_rules(id) ON DELETE RESTRICT
            );

            -- 6. Personal Radiation Dose Readings
            CREATE TABLE IF NOT EXISTS radiation_readings (
                id TEXT PRIMARY KEY,
                astronaut_id TEXT NOT NULL,
                mission_id TEXT NOT NULL,
                dosimeter_id TEXT,
                dose_type TEXT NOT NULL DEFAULT 'cumulative', -- 'rate' or 'cumulative'
                original_value REAL NOT NULL,
                original_unit TEXT NOT NULL, -- e.g., 'mSv', 'uSv/h'
                quality_status TEXT NOT NULL DEFAULT 'Valid' CHECK (quality_status IN ('Valid', 'Suspect', 'Invalid', 'Unknown')),
                measured_at TEXT NOT NULL,
                received_at TEXT NOT NULL
            );

            -- 7. Cabin Environmental Readings
            CREATE TABLE IF NOT EXISTS environmental_readings (
                id TEXT PRIMARY KEY,
                mission_id TEXT NOT NULL,
                compartment_name TEXT NOT NULL,
                parameter_name TEXT NOT NULL, -- e.g., 'O2', 'CO2', 'Pressure', 'Temperature'
                original_value REAL NOT NULL,
                original_unit TEXT NOT NULL,
                quality_status TEXT NOT NULL DEFAULT 'Valid' CHECK (quality_status IN ('Valid', 'Suspect', 'Invalid', 'Unknown')),
                measured_at TEXT NOT NULL,
                received_at TEXT NOT NULL
            );

            -- 8. Unified Synchronization Outbox (Offline-to-Cloud Queue)
            CREATE TABLE IF NOT EXISTS sync_outbox (
                event_id TEXT PRIMARY KEY,
                target_table TEXT NOT NULL, -- Supabase destination table name
                record_id TEXT NOT NULL,
                operation TEXT NOT NULL DEFAULT 'UPSERT' CHECK (operation IN ('UPSERT', 'UPDATE')),
                payload_json TEXT NOT NULL, -- Full JSON snapshot ready for Supabase upsert
                state TEXT NOT NULL DEFAULT 'pending' CHECK (state IN ('pending', 'retry', 'synced', 'failed')),
                attempts INTEGER NOT NULL DEFAULT 0,
                last_error TEXT,
                created_at TEXT NOT NULL,
                synced_at TEXT
            );

            -- Performance Indexes for Time-Series Queries & Sync Worker
            CREATE INDEX IF NOT EXISTS idx_vitals_astronaut_time ON vital_signs(astronaut_id, measured_at DESC);
            CREATE INDEX IF NOT EXISTS idx_symptoms_astronaut_time ON symptom_reports(astronaut_id, measured_at DESC);
            CREATE INDEX IF NOT EXISTS idx_alerts_status_time ON health_alerts(status, triggered_at DESC);
            CREATE INDEX IF NOT EXISTS idx_radiation_astronaut_time ON radiation_readings(astronaut_id, measured_at DESC);
            CREATE INDEX IF NOT EXISTS idx_env_compartment_time ON environmental_readings(compartment_name, measured_at DESC);
            CREATE INDEX IF NOT EXISTS idx_sync_outbox_queue ON sync_outbox(state, created_at ASC);
        """)


if __name__ == "__main__":
    initialize_database()
    print(f"Full 8-table SQLite schema initialized at: {DB_PATH}")