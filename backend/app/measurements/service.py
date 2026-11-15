from datetime import datetime
import hashlib
import json
from uuid import uuid4

from app.core.errors import AppError
from app.core.models import utc_now
from app.measurements.models import Measurement
from app.measurements.units import normalize


def ingest(
    record: Measurement,
    store,
    settings,
    actor_id: str,
) -> dict:
    raw = record.model_dump(mode="json")

    try:
        normalized = normalize(record)

        if (
            settings.environment == "production"
            and record.is_synthetic
        ):
            raise AppError(
                403,
                "synthetic_production_blocked",
                "Synthetic telemetry blocked in production",
            )

    except AppError as exc:
        store.put(
            "quarantine",
            str(uuid4()),
            {
                "raw": raw,
                "reason": exc.code,
                "received_at": utc_now().isoformat(),
            },
            mission_id=record.mission_id,
            actor_id=actor_id,
            enqueue=False,
        )
        raise

    raw.update(normalized)

    from app.alerts.service import evaluate_measurement

    conflict = None

    # Evidence, alert, incident, audit and queue commit together.
    with store.transaction():
        existing = store.get("measurement", record.event_id)

        raw["received_at"] = (
            existing["received_at"]
            if existing
            else utc_now().isoformat()
        )

        if existing:
            raw["out_of_order"] = existing.get(
                "out_of_order", False
            )

        else:
            cursor_id = hashlib.sha256(
                json.dumps([
                    record.mission_id,
                    record.astronaut_id,
                    record.metric,
                ]).encode()
            ).hexdigest()

            cursor = store.get(
                "measurement_cursor", cursor_id
            )

            if cursor is None:
                previous = [
                    row
                    for row in store.list(
                        "measurement",
                        mission_id=record.mission_id,
                    )
                    if row.get("metric") == record.metric
                    and row.get("astronaut_id")
                    == record.astronaut_id
                ]

                if previous:
                    newest = max(
                        previous,
                        key=lambda row: datetime.fromisoformat(
                            row["measured_at"].replace(
                                "Z", "+00:00"
                            )
                        ),
                    )

                    cursor = {
                        "measured_at": newest["measured_at"],
                        "event_id": newest["event_id"],
                    }

            raw["out_of_order"] = (
                cursor is not None
                and datetime.fromisoformat(
                    cursor["measured_at"].replace(
                        "Z", "+00:00"
                    )
                ) > record.measured_at
            )

        try:
            persisted = store.put(
                "measurement",
                record.event_id,
                raw,
                mission_id=record.mission_id,
                actor_id=actor_id,
                priority=50,
            )

        except AppError as exc:
            if exc.status_code != 409:
                raise
            conflict = exc

        if conflict is None:
            if not existing:
                next_cursor = (
                    cursor
                    if raw["out_of_order"]
                    else {
                        "measured_at": raw["measured_at"],
                        "event_id": raw["event_id"],
                    }
                )

                store.put(
                    "measurement_cursor",
                    cursor_id,
                    next_cursor,
                    mission_id=record.mission_id,
                    actor_id=actor_id,
                    enqueue=False,
                    immutable=False,
                )

            alerts = evaluate_measurement(
                persisted,
                store,
                settings,
                actor_id,
            )

    # Raise after commit so rejected evidence remains in the ledger.
    if conflict is not None:
        raise conflict

    return {
        "measurement": persisted,
        "duplicate": existing is not None,
        "alerts": alerts,
    }