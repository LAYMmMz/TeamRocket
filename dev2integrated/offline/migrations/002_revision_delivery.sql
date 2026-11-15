CREATE TABLE sync_queue_v2(
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
 created_at TEXT NOT NULL
);
INSERT INTO sync_queue_v2 SELECT * FROM sync_queue;
DROP TABLE sync_queue;
ALTER TABLE sync_queue_v2 RENAME TO sync_queue;
CREATE INDEX idx_queue_ready
 ON sync_queue(status,priority,available_at);
CREATE INDEX idx_queue_record_order
 ON sync_queue(kind,record_id);
