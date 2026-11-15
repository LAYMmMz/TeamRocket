"""Dev 2 staging APIs integrated into Dev 1's existing guarded Store.

Prototype API only: no automated clinical diagnosis, clearance, medication advice,
or cloud sync for these new domain2 record types until DB team contracts are signed.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from app.auth.dependencies import require
from app.core.dependencies import get_store, get_settings
from app.core.errors import AppError
from app.domain2.contracts import DomainEvent, PRIVATE_DOMAINS, DOMAIN_FIELDS, validate_domain

router = APIRouter(prefix="/domain2", tags=["Developer 2 domain prototypes"])

def privacy_gate(domain, principal):
    # Dev 1's principal trusts only server-controlled app_metadata roles.
    if domain in PRIVATE_DOMAINS and not any(role in principal.roles for role in ("admin", "flight_surgeon")):
        principal.deny("behavioral:restricted")

@router.get("/catalog")
def catalog(principal=Depends(require("foundation:read"))):
    return {"domains": list(DOMAIN_FIELDS), "status": "prototype_staging_contracts", "cloud_persistence": False}

@router.post("/{domain}", status_code=201)
def create_domain_event(
    domain: str,
    event: DomainEvent,
    principal=Depends(require("measurements:write")),
    store=Depends(get_store),
    settings=Depends(get_settings),
):
    principal.require_mission(event.mission_id)
    privacy_gate(domain, principal)
    if domain not in DOMAIN_FIELDS:
        raise HTTPException(status_code=404, detail="Unknown domain")
    if event.source_type != "SIMULATED" or settings.environment not in {"development", "test"}:
        raise AppError(403, "prototype_synthetic_only", "Domain 2 staging accepts only development synthetic events")
    try:
        record=validate_domain(domain,event)
    except (ValueError, TypeError) as exc:
        raise AppError(422, "invalid_domain_contract", str(exc)) from None
    kind="dev2_"+domain
    existing=store.get(kind,event.event_id)
    if existing is not None and existing != record:
        raise AppError(409, "immutable_event_conflict", "Earlier evidence preserved")
    # Deliberately not enqueued for Supabase until cloud destination mapping is reviewed.
    # Serious symptoms must use the existing shared incident engine, including
    # when SpO2 or all other sensor data is absent. Never re-implement alerts.
    incident = None
    if domain == "symptoms" and event.data["severity_category"] in {"serious", "severe", "critical"}:
        from app.incidents.service import ingest_serious_symptom
        incident = ingest_serious_symptom({
            "event_id": event.event_id, "mission_id": event.mission_id,
            "astronaut_id": event.astronaut_id, "symptom": event.data["symptom_code"],
            "severity": event.data["severity_category"],
            "onset": event.data["onset_at"], "body_location": event.data["body_location"],
            "source_type": event.source_type, "is_synthetic": event.is_synthetic,
            "measured_at": event.measured_at, "received_at": event.received_at,
            "quality": event.quality, "verification": event.verification,
        }, store, settings, principal.user_id)
    result=store.put(kind,event.event_id,record,mission_id=event.mission_id,actor_id=principal.user_id,enqueue=False)
    return {"event": result,"duplicate":existing is not None,
            "incident": incident, "cloud_sync":"not_configured_for_domain2"}

@router.get("/{domain}")
def list_domain_events(
    domain: str, mission_id: str,
    principal=Depends(require("measurements:read")),
    store=Depends(get_store),
):
    principal.require_mission(mission_id)
    privacy_gate(domain,principal)
    if domain not in DOMAIN_FIELDS:
        raise HTTPException(status_code=404, detail="Unknown domain")
    return {"items":store.list("dev2_"+domain,mission_id=mission_id),"cloud_sync":"not_configured_for_domain2"}
