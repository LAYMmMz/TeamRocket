from datetime import datetime, timezone
from contextlib import nullcontext
from uuid import NAMESPACE_URL, uuid5
import json
from pydantic import ValidationError

from app.core.errors import AppError
from app.incidents.models import SeriousSymptom


def _id(*parts):
    return str(uuid5(
        NAMESPACE_URL,
        json.dumps(parts, separators=(",", ":"))
    ))


def _now():
    return datetime.now(timezone.utc).isoformat()


def _parse(value):
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(
        str(value).replace("Z", "+00:00")
    )


def incident_timeline(store, incident_id):
    return sorted(
        [
            item for item in store.list("incident_event")
            if item.get("incident_id") == incident_id
        ],
        key=lambda item: (item["recorded_at"], item["event_id"]),
    )


def link_alert(alert, rule, store, actor_id):
    context = (
        store.transaction()
        if hasattr(store, "transaction") else nullcontext()
    )
    with context:
        return _link_alert(alert, rule, store, actor_id)


def _link_alert(alert, rule, store, actor_id):
    mission_id = alert["mission_id"]
    astronaut_id = alert.get("astronaut_id")
    explicit_correlation = rule.get("correlation_key")
    correlation = explicit_correlation or rule["rule_id"]
    incident_event_id = _id("alert-link", alert["event_id"])
    previous = store.get("incident_event", incident_event_id)
    if previous:
        return store.get("incident", previous["incident_id"])

    candidate = None
    if alert["severity"] != "critical":
        for item in store.list("incident", mission_id=mission_id):
            if item.get("correlation_key") != correlation:
                continue
            item_astro = item.get("astronaut_id")
            same_astronaut = item_astro == astronaut_id
            habitat_to_crew_match = bool(explicit_correlation) and (
                item_astro is None or astronaut_id is None
            )
            if not (same_astronaut or habitat_to_crew_match):
                continue
            elapsed = abs((
                _parse(alert["received_at"])
                - _parse(item["received_at"])
            ).total_seconds())
            if elapsed > rule.get("correlation_window_seconds", 3600):
                continue
            chronology = incident_timeline(
                store, item["incident_id"]
            )
            states = [
                event for event in chronology
                if event["kind"] in {"CLOSED", "REOPENED"}
            ]
            if states and states[-1]["kind"] == "CLOSED":
                continue
            candidate = item
            break

    incident_id = (
        candidate["incident_id"] if candidate
        else _id("incident", alert["event_id"])
    )
    if candidate is None:
        candidate = {
            "incident_id": incident_id,
            "event_id": incident_id,
            "mission_id": mission_id,
            "astronaut_id": astronaut_id,
            "correlation_key": correlation,
            "severity": alert["severity"],
            "source_type": alert["source_type"],
            "is_synthetic": alert["is_synthetic"],
            "measured_at": alert["measured_at"],
            "received_at": alert["received_at"],
            "quality": alert["quality"],
            "verification": alert["verification"],
            "label": alert["label"],
            "status": "OPEN",
            "correlation_note": (
                "Linked evidence; correlation does not establish causality."
            ),
        }
        store.put(
            "incident", incident_id, candidate,
            mission_id=mission_id, actor_id=actor_id,
            priority=0 if alert["severity"] == "critical" else 25,
        )
    elif candidate.get("astronaut_id") is None and astronaut_id is not None:
        updated = {**candidate, "astronaut_id": astronaut_id}
        store.put(
            "incident", incident_id, updated,
            mission_id=mission_id, actor_id=actor_id,
            priority=0 if alert["severity"] == "critical" else 25,
        )
        candidate = updated

    entry = {
        "event_id": incident_event_id,
        "incident_id": incident_id,
        "mission_id": mission_id,
        "kind": "EVIDENCE_LINKED",
        "alert_id": alert["event_id"],
        "evidence_event_id": alert["evidence_event_id"],
        "recorded_at": _now(),
        "measured_at": alert["measured_at"],
        "received_at": alert["received_at"],
        "source_type": alert["source_type"],
        "is_synthetic": alert["is_synthetic"],
        "quality": alert["quality"],
        "verification": alert["verification"],
        "actor_id": actor_id,
    }
    store.put(
        "incident_event", incident_event_id, entry,
        mission_id=mission_id, actor_id=actor_id,
        priority=0 if alert["severity"] == "critical" else 25,
    )
    return candidate


def ingest_serious_symptom(payload, store, settings, actor_id):
    conflict = None
    result = None
    context = (
        store.transaction()
        if hasattr(store, "transaction") else nullcontext()
    )
    with context:
        try:
            result = _ingest_serious_symptom(
                payload, store, settings, actor_id
            )
        except AppError as exc:
            if exc.status_code != 409:
                raise
            conflict = exc
    if conflict is not None:
        raise conflict
    return result


def _ingest_serious_symptom(payload, store, settings, actor_id):
    try:
        payload = SeriousSymptom.model_validate(
            payload
        ).model_dump(mode="json")
    except ValidationError as exc:
        raise AppError(
            422, "invalid_symptom", "Invalid symptom metadata",
            details=str(exc)
        ) from exc

    if (
        payload["is_synthetic"]
        and settings.environment not in {"development", "test"}
    ):
        raise AppError(
            403, "synthetic_data_disabled", "Synthetic data disabled"
        )
    mission_id = payload["mission_id"]
    if payload["severity"] not in {"serious", "critical", "severe"}:
        raise AppError(422, "invalid_symptom", "Invalid severity")

    required = {
        "measured_at", "received_at", "quality",
        "verification", "source_type", "is_synthetic"
    }
    symptom_id = payload["event_id"]
    store.put(
        "symptom_report", symptom_id, payload,
        mission_id=mission_id, actor_id=actor_id, priority=0
    )

    alert_id = _id("serious-symptom", symptom_id)
    alert = store.get("health_alert", alert_id)
    if alert is None:
        alert = {
            "event_id": alert_id,
            "evidence_event_id": symptom_id,
            "mission_id": mission_id,
            "astronaut_id": payload.get("astronaut_id"),
            "severity": "critical",
            "kind": "SYMPTOM_ESCALATION",
            "mode": "WORKFLOW",
            "operational": False,
            "label": (
                "SIMULATED" if payload["is_synthetic"]
                else "REVIEW REQUIRED"
            ),
            "message": (
                "Serious symptom reported. Contact the designated "
                "clinician or mission emergency channel for human review."
            ),
            "rule_snapshot": None,
            "evidence_snapshot": payload,
            "sensor_corroboration_required": False,
            **{key: payload[key] for key in required},
        }
        store.put(
            "health_alert", alert_id, alert,
            mission_id=mission_id, actor_id=actor_id, priority=0
        )
    return link_alert(
        alert, {"rule_id": "serious-symptom-workflow"},
        store, actor_id
    )