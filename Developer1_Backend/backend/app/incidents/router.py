from fastapi import APIRouter, Depends
from app.auth.dependencies import require
from app.core.dependencies import get_settings, get_store
from app.core.errors import AppError
from app.incidents.service import (
    incident_timeline, ingest_serious_symptom, _now
)
from app.incidents.models import SeriousSymptom, IncidentEvent

router = APIRouter(prefix="/incidents", tags=["incident chronology"])

def _incident(store, principal, incident_id):
    item = store.get("incident", incident_id)
    if item is None:
        raise AppError(404, "not_found", "Incident not found")
    principal.require_mission(item["mission_id"])
    return item

def _projection(store, item):
    events = incident_timeline(store, item["incident_id"])
    states = [
        event for event in events
        if event["kind"] in {"CLOSED", "REOPENED"}
    ]
    rank = {
        "information": 0, "data-unavailable": 1,
        "advisory": 2, "warning": 3, "critical": 4
    }
    severities = [item["severity"]]
    for event in events:
        if event.get("alert_id"):
            alert = store.get("health_alert", event["alert_id"])
            if alert:
                severities.append(alert["severity"])
    return {
        **item,
        "severity": max(severities, key=lambda value: rank[value]),
        "status": (
            "CLOSED" if states and states[-1]["kind"] == "CLOSED"
            else "OPEN"
        ),
        "timeline_count": len(events),
    }

@router.post("/serious-symptoms", status_code=201)
def serious_symptom(
    data: SeriousSymptom,
    principal=Depends(require("measurements:write")),
    store=Depends(get_store),
    settings=Depends(get_settings),
):
    principal.require_mission(data.mission_id)
    if (
        data.is_synthetic
        and settings.environment not in {"development", "test"}
    ):
        raise AppError(
            403, "synthetic_data_disabled", "Synthetic data disabled"
        )
    return ingest_serious_symptom(
        data.model_dump(mode="json"),
        store, settings, principal.user_id
    )

@router.get("")
def list_incidents(
    mission_id: str,
    principal=Depends(require("incidents:read")),
    store=Depends(get_store),
):
    principal.require_mission(mission_id)
    return {
        "items": [
            _projection(store, item)
            for item in store.list("incident", mission_id=mission_id)
        ]
    }

@router.get("/{incident_id}")
def get_incident(
    incident_id: str,
    principal=Depends(require("incidents:read")),
    store=Depends(get_store),
):
    return _projection(
        store, _incident(store, principal, incident_id)
    )

@router.get("/{incident_id}/timeline")
def get_timeline(
    incident_id: str,
    principal=Depends(require("incidents:read")),
    store=Depends(get_store),
):
    _incident(store, principal, incident_id)
    return {"items": incident_timeline(store, incident_id)}

@router.post("/{incident_id}/events", status_code=201)
def add_event(
    incident_id: str,
    data: IncidentEvent,
    principal=Depends(require("incidents:write")),
    store=Depends(get_store),
):
    incident = _incident(store, principal, incident_id)
    previous = store.get("incident_event", data.event_id)
    if previous:
        if (
            previous.get("incident_id") != incident_id
            or previous.get("kind") != data.kind
            or previous.get("note") != data.note
            or previous.get("actor_id") != principal.user_id
        ):
            raise AppError(
                409, "event_conflict", "Event conflict"
            )
        return previous

    item = {
        **data.model_dump(),
        "incident_id": incident_id,
        "mission_id": incident["mission_id"],
        "recorded_at": _now(),
        "actor_id": principal.user_id,
        **{
            key: incident[key] for key in [
                "source_type", "is_synthetic",
                "measured_at", "received_at",
                "quality", "verification"
            ]
        },
    }
    return store.put(
        "incident_event", data.event_id, item,
        mission_id=incident["mission_id"],
        actor_id=principal.user_id,
    )
