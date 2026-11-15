import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from database import get_db, initialize_database
from sync import sync_pending_records

initialize_database()

app = FastAPI(title="NASA Astronaut Health Offline-First API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class VitalSignIn(BaseModel):
    astronaut_id: str = Field(min_length=1, max_length=64)
    mission_id: str = Field(default="ARTEMIS-DEMO", max_length=64)
    metric_code: str = Field(default="heart_rate", max_length=32)
    value: float
    unit: str = Field(default="bpm", max_length=16)
    source_device_id: Optional[str] = "BIO-SENSOR-01"


class SymptomIn(BaseModel):
    astronaut_id: str = Field(min_length=1, max_length=64)
    mission_id: str = Field(default="ARTEMIS-DEMO", max_length=64)
    symptom_code: str = Field(min_length=1, max_length=64)
    severity: int = Field(ge=1, le=10)
    notes: Optional[str] = None


def _enqueue_outbox(db, target_table: str, record_id: str, payload: dict, now_iso: str):
    db.execute(
        """
        INSERT INTO sync_outbox (event_id, target_table, record_id, operation, payload_json, state, created_at)
        VALUES (?, ?, ?, 'UPSERT', ?, 'pending', ?)
        """,
        (str(uuid.uuid4()), target_table, record_id, json.dumps(payload), now_iso),
    )


@app.post("/vitals")
def record_vital_sign(data: VitalSignIn):
    record_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    record = {
        "id": record_id,
        "astronaut_id": data.astronaut_id,
        "mission_id": data.mission_id,
        "source_device_id": data.source_device_id,
        "source_type": "Automated Telemetry",
        "metric_code": data.metric_code,
        "original_value": data.value,
        "original_unit": data.unit,
        "normalized_value": data.value,
        "normalized_unit": data.unit,
        "quality_status": "Valid",
        "measured_at": now_iso,
        "received_at": now_iso,
    }

    with get_db() as db:
        db.execute(
            """
            INSERT INTO vital_signs (
                id, astronaut_id, mission_id, source_device_id, source_type,
                metric_code, original_value, original_unit, normalized_value,
                normalized_unit, quality_status, measured_at, received_at
            ) VALUES (
                :id, :astronaut_id, :mission_id, :source_device_id, :source_type,
                :metric_code, :original_value, :original_unit, :normalized_value,
                :normalized_unit, :quality_status, :measured_at, :received_at
            )
            """,
            record,
        )
        _enqueue_outbox(db, "vital_signs", record_id, record, now_iso)

    return {"saved_locally": True, "record_id": record_id, "sync_status": "pending"}


@app.get("/vitals")
def get_vital_signs(limit: int = 50):
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM vital_signs ORDER BY measured_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


@app.post("/symptoms")
def record_symptom(data: SymptomIn):
    record_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    record = {
        "id": record_id,
        "astronaut_id": data.astronaut_id,
        "mission_id": data.mission_id,
        "symptom_code": data.symptom_code,
        "severity": data.severity,
        "notes": data.notes,
        "measured_at": now_iso,
        "received_at": now_iso,
    }

    with get_db() as db:
        db.execute(
            """
            INSERT INTO symptom_reports (
                id, astronaut_id, mission_id, symptom_code, severity, notes, measured_at, received_at
            ) VALUES (
                :id, :astronaut_id, :mission_id, :symptom_code, :severity, :notes, :measured_at, :received_at
            )
            """,
            record,
        )
        _enqueue_outbox(db, "symptom_reports", record_id, record, now_iso)

    return {"saved_locally": True, "record_id": record_id, "sync_status": "pending"}


@app.get("/sync/status")
def get_sync_status():
    with get_db() as db:
        rows = db.execute(
            "SELECT state, COUNT(*) AS count FROM sync_outbox GROUP BY state"
        ).fetchall()
        return {row["state"]: row["count"] for row in rows}


@app.post("/sync")
def trigger_sync():
    return sync_pending_records()