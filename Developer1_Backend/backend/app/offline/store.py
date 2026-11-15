from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

from cryptography.fernet import Fernet, InvalidToken
from app.core.errors import AppError

def utcnow():
    return datetime.now(timezone.utc).isoformat()

def canonical(payload):
    def encode(value):
        if hasattr(value, "model_dump"):
            return value.model_dump(mode="json")
        if isinstance(value, datetime):
            return value.isoformat()
        if hasattr(value, "value"):
            return value.value
        return str(value)
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"),
        allow_nan=False, default=encode
    ).encode()

_TABLES = {
    "measurement": "offline_vital_signs",
    "measurements": "offline_vital_signs",
    "vital": "offline_vital_signs",
    "vitals": "offline_vital_signs",
    "symptom_report": "offline_symptom_reports",
    "symptom_reports": "offline_symptom_reports",
    "symptom": "offline_symptom_reports",
    "alert": "offline_health_alerts",
    "alerts": "offline_health_alerts",
    "health_alert": "offline_health_alerts",
    "rule": "offline_alert_rules",
    "rules": "offline_alert_rules",
    "alert_rule": "offline_alert_rules",
    "procedure": "offline_medical_procedures",
    "procedures": "offline_medical_procedures",
    "medical_procedure": "offline_medical_procedures",
}

class Store:
    def __init__(self, settings):
        self.path = Path(settings.sqlite_path).expanduser().resolve()
        self.path.parent.mkdir(
            parents=True, exist_ok=True, mode=0o700
        )
        self._lock = threading.RLock()
        key = settings.encryption_key

        if not key:
            if settings.environment not in {"development", "test"}:
                raise AppError(
                    503, "encryption_key_required",
                    "External encryption key required"
                )
            key_path = Path(str(self.path) + ".key")
            try:
                fd = os.open(
                    key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                    0o600
                )
            except FileExistsError:
                key = key_path.read_bytes()
            else:
                key = Fernet.generate_key()
                with os.fdopen(fd, "wb") as handle:
                    handle.write(key)
                    handle.flush()
                    os.fsync(handle.fileno())
            os.chmod(key_path, 0o600)

        if isinstance(key, str):
            key = key.encode()
        try:
            self._cipher = Fernet(key)
        except (TypeError, ValueError) as exc:
            raise AppError(
                503, "invalid_encryption_key", "Invalid encryption key"
            ) from exc

        self._db = sqlite3.connect(
            self.path, check_same_thread=False, timeout=30
        )
        os.chmod(self.path, 0o600)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA synchronous=FULL")
        self._db.execute("PRAGMA foreign_keys=ON")
        self._db.execute("PRAGMA busy_timeout=30000")

        migrations = (
            Path(__file__).resolve().parents[2]
            / "offline" / "migrations"
        )
        with self._lock:
            self._db.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations("
                "version INTEGER PRIMARY KEY,applied_at TEXT NOT NULL)"
            )
            self._db.commit()
            applied = {
                row[0] for row in self._db.execute(
                    "SELECT version FROM schema_migrations"
                )
            }
            for migration in sorted(migrations.glob("*.sql")):
                version = int(migration.name.split("_", 1)[0])
                if version in applied:
                    continue
                try:
                    self._db.executescript(
                        "BEGIN IMMEDIATE;\n"
                        + migration.read_text(encoding="utf-8")
                    )
                    self._db.execute(
                        "INSERT INTO schema_migrations VALUES (?,?)",
                        (version, utcnow()),
                    )
                    self._db.commit()
                except Exception:
                    self._db.rollback()
                    self._db.close()
                    raise

            try:
                for table in [
                    "durable_records", "offline_vital_signs",
                    "offline_symptom_reports", "offline_health_alerts",
                    "offline_alert_rules", "offline_medical_procedures"
                ]:
                    row = self._db.execute(
                        f"SELECT payload FROM {table} LIMIT 1"
                    ).fetchone()
                    if row:
                        self._decode(row["payload"])
            except Exception:
                self._db.close()
                raise

    @property
    def schema_version(self):
        with self._lock:
            return self._db.execute(
                "SELECT MAX(version) FROM schema_migrations"
            ).fetchone()[0]

    def _decode(self, encrypted):
        try:
            return json.loads(self._cipher.decrypt(encrypted))
        except (InvalidToken, ValueError) as exc:
            raise AppError(
                503, "local_decryption_failed",
                "Local decryption failed"
            ) from exc

    def _encode(self, value):
        return self._cipher.encrypt(canonical(value))

    @contextmanager
    def transaction(self):
        with self._lock:
            nested = self._db.in_transaction
            savepoint = "sp_" + uuid.uuid4().hex
            self._db.execute(
                f"SAVEPOINT {savepoint}" if nested
                else "BEGIN IMMEDIATE"
            )
            try:
                yield self._db
            except Exception:
                if nested:
                    self._db.execute(
                        f"ROLLBACK TO SAVEPOINT {savepoint}"
                    )
                    self._db.execute(
                        f"RELEASE SAVEPOINT {savepoint}"
                    )
                else:
                    self._db.rollback()
                raise
            else:
                if nested:
                    self._db.execute(
                        f"RELEASE SAVEPOINT {savepoint}"
                    )
                else:
                    self._db.commit()

    def _audit(
        self, db, action, actor_id,
        mission_id=None, record_id=None, details=None
    ):
        identifier = str(uuid.uuid4())
        payload = {
            "id": identifier,
            "action": action,
            "actor_id": actor_id,
            "mission_id": mission_id,
            "record_id": record_id,
            "details": details or {},
            "received_at": utcnow(),
        }
        encoded = canonical(payload)
        db.execute(
            "INSERT INTO durable_records VALUES (?,?,?,?,?,?)",
            (
                "audit", identifier, mission_id,
                self._cipher.encrypt(encoded),
                hashlib.sha256(encoded).hexdigest(), utcnow()
            ),
        )
        return payload

    def _enqueue(
        self, db, kind, record_id, mission_id,
        data, digest, audit, priority,
        immutable=True, previous_hash=None
    ):
        identity = f"{kind}\0{record_id}\0{digest}"
        if not immutable:
            revision = db.execute(
                "SELECT COUNT(*) FROM sync_queue "
                "WHERE kind=? AND record_id=?",
                (kind, record_id),
            ).fetchone()[0] + 1
            identity += f"\0revision:{revision}"

        queue_id = hashlib.sha256(identity.encode()).hexdigest()
        remote_event_id = (
            f"{kind}:{record_id}"
            + (f":{queue_id}" if not immutable else "")
        )
        envelope = {
            "payload": data,
            "audit_event": audit,
            "immutable": immutable,
            "previous_hash": previous_hash,
            "remote_event_id": remote_event_id,
        }
        db.execute(
            "INSERT OR IGNORE INTO sync_queue("
            "queue_id,kind,record_id,mission_id,payload,payload_hash,"
            "priority,status,attempts,available_at,created_at"
            ") VALUES (?,?,?,?,?,?,?,'pending',0,?,?)",
            (
                queue_id, kind, record_id, mission_id,
                self._encode(envelope), digest,
                int(priority), time.time(), utcnow()
            ),
        )

    def audit(
        self, action, actor_id, *,
        mission_id=None, record_id=None, details=None
    ):
        with self.transaction() as db:
            payload = self._audit(
                db, action, actor_id, mission_id, record_id, details
            )
            digest = hashlib.sha256(canonical(payload)).hexdigest()
            self._enqueue(
                db, "audit", payload["id"], mission_id,
                payload, digest, None, 200
            )
            return payload

    def put(
        self, kind, record_id, payload, *,
        mission_id=None, actor_id="system",
        enqueue=True, priority=100, immutable=True
    ):
        kind, record_id = str(kind), str(record_id)
        data = json.loads(canonical(payload))
        if mission_id is None and isinstance(data, dict):
            mission_id = data.get("mission_id")
        raw = canonical(data)
        digest = hashlib.sha256(raw).hexdigest()
        table = _TABLES.get(kind, "durable_records")
        conflict = False

        with self.transaction() as db:
            existing = db.execute(
                f"SELECT payload,payload_hash FROM {table} "
                "WHERE kind=? AND record_id=?",
                (kind, record_id),
            ).fetchone()

            if existing and existing["payload_hash"] == digest:
                return self._decode(existing["payload"])

            if existing and immutable:
                conflict_id = str(uuid.uuid4())
                db.execute(
                    "INSERT INTO conflict_ledger VALUES "
                    "(?,?,?,?,?,?,?,?,?)",
                    (
                        conflict_id, kind, record_id, mission_id,
                        existing["payload_hash"], digest,
                        self._cipher.encrypt(raw),
                        str(actor_id), utcnow()
                    ),
                )
                self._audit(
                    db, "conflict.rejected", actor_id,
                    mission_id, record_id,
                    {"kind": kind, "conflict_id": conflict_id}
                )
                conflict = True
            else:
                db.execute(
                    f"INSERT INTO {table} VALUES (?,?,?,?,?,?) "
                    "ON CONFLICT(kind,record_id) DO UPDATE SET "
                    "mission_id=excluded.mission_id,"
                    "payload=excluded.payload,"
                    "payload_hash=excluded.payload_hash,"
                    "stored_at=excluded.stored_at",
                    (
                        kind, record_id, mission_id,
                        self._cipher.encrypt(raw), digest, utcnow()
                    ),
                )
                audit = self._audit(
                    db, f"{kind}.write", actor_id,
                    mission_id, record_id,
                    {"payload_hash": digest}
                )
                if enqueue:
                    self._enqueue(
                        db, kind, record_id, mission_id,
                        data, digest, audit, priority,
                        immutable=immutable,
                        previous_hash=(
                            existing["payload_hash"]
                            if existing else None
                        ),
                    )

        if conflict:
            raise AppError(
                409, "event_conflict",
                "Original evidence preserved",
                {"record_id": record_id},
            )
        return data

    def get(self, kind, record_id):
        if kind in {"conflict", "conflicts"}:
            return next(
                (
                    item for item in self.conflicts()
                    if item["conflict_id"] == str(record_id)
                ),
                None,
            )
        table = _TABLES.get(kind, "durable_records")
        with self._lock:
            row = self._db.execute(
                f"SELECT payload FROM {table} "
                "WHERE kind=? AND record_id=?",
                (str(kind), str(record_id)),
            ).fetchone()
            return self._decode(row["payload"]) if row else None

    def list(self, kind, *, mission_id=None):
        if kind in {"conflict", "conflicts"}:
            return self.conflicts(mission_id=mission_id)
        table = _TABLES.get(kind, "durable_records")
        query = f"SELECT payload FROM {table} WHERE kind=?"
        args = [str(kind)]
        if mission_id is not None:
            query += " AND mission_id=?"
            args.append(str(mission_id))
        query += " ORDER BY stored_at,record_id"
        with self._lock:
            rows = self._db.execute(query, args).fetchall()
            return [self._decode(row["payload"]) for row in rows]

    @property
    def pending_count(self):
        counts = self.queue_status()["counts"]
        return sum(
            counts.get(key, 0)
            for key in ("pending", "retry", "sending")
        )

    def queue_status(self, mission_ids=None):
        query = "SELECT status,COUNT(*) AS n FROM sync_queue"
        args = []
        if mission_ids is not None:
            if not mission_ids:
                return {"counts": {}}
            query += (
                " WHERE mission_id IN ("
                + ",".join("?" for _ in mission_ids) + ")"
            )
            args = list(mission_ids)
        query += " GROUP BY status"
        with self._lock:
            counts = {
                row["status"]: row["n"]
                for row in self._db.execute(query, args)
            }
        return {"counts": counts}

    def claim_batch(
        self, limit, mission_ids=None,
        lease_seconds=60, max_attempts=5
    ):
        now = time.time()
        with self.transaction() as db:
            db.execute(
                "UPDATE sync_queue SET status=CASE WHEN attempts>=? "
                "THEN 'dead' ELSE 'retry' END,claimed_at=NULL "
                "WHERE status='sending' AND claimed_at < ?",
                (max_attempts, now - lease_seconds),
            )
            db.execute(
                "UPDATE sync_queue SET status='dead' "
                "WHERE status IN ('pending','retry') AND attempts>=?",
                (max_attempts,),
            )
            query = (
                "SELECT q.* FROM sync_queue AS q "
                "WHERE q.status IN ('pending','retry') "
                "AND q.available_at <= ? "
                "AND NOT EXISTS (SELECT 1 FROM sync_queue AS earlier "
                "WHERE earlier.kind=q.kind "
                "AND earlier.record_id=q.record_id "
                "AND earlier.rowid<q.rowid "
                "AND earlier.status!='synced')"
            )
            args = [now]
            if mission_ids is not None:
                if not mission_ids:
                    return []
                query += (
                    " AND q.mission_id IN ("
                    + ",".join("?" for _ in mission_ids) + ")"
                )
                args += list(mission_ids)
            query += (
                " ORDER BY priority ASC,created_at ASC,queue_id ASC "
                "LIMIT ?"
            )
            args.append(int(limit))
            result = []
            for row in db.execute(query, args).fetchall():
                db.execute(
                    "UPDATE sync_queue SET status='sending',"
                    "attempts=attempts+1,claimed_at=? WHERE queue_id=?",
                    (now, row["queue_id"]),
                )
                item = dict(row)
                envelope = self._decode(row["payload"])
                item["payload"] = envelope["payload"]
                item["audit_event"] = envelope["audit_event"]
                item["immutable"] = envelope.get("immutable", True)
                item["previous_hash"] = envelope.get("previous_hash")
                item["remote_event_id"] = (
                    envelope.get("remote_event_id")
                    or f"{row['kind']}:{row['record_id']}"
                    + (
                        f":{row['payload_hash']}"
                        if not item["immutable"] else ""
                    )
                )
                item["attempts"] += 1
                result.append(item)
            return result

    def mark_synced(
        self, queue_id, receipt, expected_attempt=None
    ):
        with self.transaction() as db:
            query = (
                "UPDATE sync_queue SET status='synced',receipt=?,"
                "claimed_at=NULL,last_error=NULL "
                "WHERE queue_id=? AND status='sending'"
            )
            args = [self._encode(receipt), queue_id]
            if expected_attempt is not None:
                query += " AND attempts=?"
                args.append(expected_attempt)
            db.execute(query, args)

    def mark_failed(
        self, queue_id, max_attempts=5,
        error="remote_unavailable", expected_attempt=None
    ):
        with self.transaction() as db:
            row = db.execute(
                "SELECT attempts,status FROM sync_queue "
                "WHERE queue_id=?", (queue_id,)
            ).fetchone()
            if (
                row and row["status"] == "sending"
                and (
                    expected_attempt is None
                    or row["attempts"] == expected_attempt
                )
            ):
                dead = row["attempts"] >= max_attempts
                delay = min(300, 2 ** min(row["attempts"], 8))
                db.execute(
                    "UPDATE sync_queue SET status=?,available_at=?,"
                    "claimed_at=NULL,last_error=? WHERE queue_id=?",
                    (
                        "dead" if dead else "retry",
                        time.time() + delay, str(error)[:120], queue_id
                    ),
                )

    def receipt(self, kind, record_id):
        with self._lock:
            row = self._db.execute(
                "SELECT receipt FROM sync_queue "
                "WHERE kind=? AND record_id=? AND status='synced' "
                "ORDER BY created_at DESC LIMIT 1",
                (kind, str(record_id)),
            ).fetchone()
            return self._decode(row["receipt"]) if row else None

    def conflicts(self, *, mission_id=None):
        query = "SELECT * FROM conflict_ledger"
        args = []
        if mission_id is not None:
            query += " WHERE mission_id=?"
            args.append(mission_id)
        with self._lock:
            result = []
            for row in self._db.execute(query, args):
                item = dict(row)
                item["incoming_payload"] = self._decode(
                    item["incoming_payload"]
                )
                result.append(item)
            return result

    def close(self):
        with self._lock:
            self._db.close()
