CREATE TABLE IF NOT EXISTS schema_migrations(
 version INTEGER PRIMARY KEY,
 applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS offline_vital_signs(
 kind TEXT NOT NULL, record_id TEXT NOT NULL, mission_id TEXT,
 payload BLOB NOT NULL, payload_hash TEXT NOT NULL,
 stored_at TEXT NOT NULL, PRIMARY KEY(kind,record_id)
);
CREATE TABLE IF NOT EXISTS offline_symptom_reports(
 kind TEXT NOT NULL, record_id TEXT NOT NULL, mission_id TEXT,
 payload BLOB NOT NULL, payload_hash TEXT NOT NULL,
 stored_at TEXT NOT NULL, PRIMARY KEY(kind,record_id)
);
CREATE TABLE IF NOT EXISTS offline_health_alerts(
 kind TEXT NOT NULL, record_id TEXT NOT NULL, mission_id TEXT,
 payload BLOB NOT NULL, payload_hash TEXT NOT NULL,
 stored_at TEXT NOT NULL, PRIMARY KEY(kind,record_id)
);
CREATE TABLE IF NOT EXISTS offline_alert_rules(
 kind TEXT NOT NULL, record_id TEXT NOT NULL, mission_id TEXT,
 payload BLOB NOT NULL, payload_hash TEXT NOT NULL,
 stored_at TEXT NOT NULL, PRIMARY KEY(kind,record_id)
);
CREATE TABLE IF NOT EXISTS offline_medical_procedures(
 kind TEXT NOT NULL, record_id TEXT NOT NULL, mission_id TEXT,
 payload BLOB NOT NULL, payload_hash TEXT NOT NULL,
 stored_at TEXT NOT NULL, PRIMARY KEY(kind,record_id)
);
CREATE TABLE IF NOT EXISTS durable_records(
 kind TEXT NOT NULL, record_id TEXT NOT NULL, mission_id TEXT,
 payload BLOB NOT NULL, payload_hash TEXT NOT NULL,
 stored_at TEXT NOT NULL, PRIMARY KEY(kind,record_id)
);
CREATE INDEX IF NOT EXISTS idx_durable_mission
 ON durable_records(kind,mission_id);

CREATE TABLE IF NOT EXISTS sync_queue(
 queue_id TEXT PRIMARY KEY,
 kind TEXT NOT NULL,
 record_id TEXT NOT NULL,
 mission_id TEXT,
 payload BLOB NOT NULL,
 payload_hash TEXT NOT NULL,
 priority INTEGER NOT NULL,
 status TEXT NOT NULL DEFAULT 'pending'
  CHECK(status IN ('pending','sending','retry','synced','dead')),
 attempts INTEGER NOT NULL DEFAULT 0,
 available_at REAL NOT NULL,
 claimed_at REAL,
 receipt BLOB,
 last_error TEXT,
 created_at TEXT NOT NULL,
 UNIQUE(kind,record_id,payload_hash)
);
CREATE INDEX IF NOT EXISTS idx_queue_ready
 ON sync_queue(status,priority,available_at);

CREATE TABLE IF NOT EXISTS conflict_ledger(
 conflict_id TEXT PRIMARY KEY,
 kind TEXT NOT NULL,
 record_id TEXT NOT NULL,
 mission_id TEXT,
 original_hash TEXT NOT NULL,
 incoming_hash TEXT NOT NULL,
 incoming_payload BLOB NOT NULL,
 actor_id TEXT NOT NULL,
 recorded_at TEXT NOT NULL
);
