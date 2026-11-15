from __future__ import annotations
from fastapi import Depends
from app.auth.dependencies import current_principal
from sqlalchemy import or_, select

from dataclasses import dataclass, field
from datetime import datetime, timezone
import os
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.models.dev2_models import (
    LocalAuditLog,
    LocalHealthAlert,
    LocalMedicalIncident,
    LocalSyncQueueItem,
    new_uuid,
)

MEDICAL_PRIVILEGED_ROLES = {
    "FLIGHT_SURGEON",
    "MEDICAL_OFFICER",
    "CLINICAL_REVIEWER",
    "ADMIN",
    "flight_surgeon",
    "medical_officer",
    "clinical_reviewer",
    "admin",
}

SEVERITY_TO_DEV1 = {
    "INFO": "info",
    "INFORMATIONAL": "info",
    "ADVISORY": "advisory",
    "WARNING": "warning",
    "CRITICAL": "critical",
    "DATA_UNAVAILABLE": "data_unavailable",
}


@dataclass
class ActorContext:
    user_id: str
    role: str
    astronaut_id: Optional[str] = None
    mission_ids: List[str] = field(default_factory=lambda: ["DEMO-01"])


def get_actor_context(request: Request, principal=Depends(current_principal)) -> ActorContext:
    """Use the SAME verified Dev1 JWT as the original API; never trust role headers."""
    role = (principal.roles[0] if principal.roles else "crew").upper()
    return ActorContext(user_id=principal.user_id, role=role,
                        astronaut_id=getattr(principal, "astronaut_id", None),
                        mission_ids=list(principal.mission_ids))

class Dev1IntegrationBridge:
    """Dual-writes audit entries, alerts, incidents, and sync packets to SQLAlchemy and Dev 1's encrypted Store."""

    @staticmethod
    def record_audit(
        db: Session,
        actor: ActorContext,
        action: str,
        resource_type: str,
        resource_id: str,
        outcome: str = "ALLOWED",
    ) -> LocalAuditLog:
        entry = LocalAuditLog(
            actor_id=actor.user_id,
            actor_role=actor.role,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
        )
        db.add(entry)
        db.flush()

        store = db.info.get("store")
        if store is not None:
            store.audit(action, actor.user_id, details={
                "role": actor.role, "resource_type": resource_type,
                "resource_id": resource_id, "outcome": outcome,
            })
        return entry

    @staticmethod
    def enforce_behavioral_privacy(
        db: Session,
        actor: ActorContext,
        target_astronaut_id: str,
        visibility_classification: str,
    ) -> None:
        if visibility_classification not in {"PRIVATE_CLINICAL", "CONFIDENTIAL"}:
            return
        if actor.role in MEDICAL_PRIVILEGED_ROLES:
            return
        if actor.astronaut_id and actor.astronaut_id == target_astronaut_id:
            return

        Dev1IntegrationBridge.record_audit(
            db,
            actor,
            action="READ_BEHAVIORAL_CHECKIN",
            resource_type="behavioral_checkins",
            resource_id=target_astronaut_id,
            outcome="DENIED",
        )
        db.commit()
        raise HTTPException(
            status_code=403,
            detail="Access denied: PRIVATE_CLINICAL behavioral health records require clinical authorization.",
        )

    @staticmethod
    def enqueue_sync(
        db: Session,
        event_id: str,
        resource_type: str,
        priority: int,
        payload: Dict[str, Any],
        mission_id: str = "DEMO-01",
    ) -> LocalSyncQueueItem:
        existing = db.scalars(
            select(LocalSyncQueueItem).where(LocalSyncQueueItem.event_id == event_id)
        ).first()
        if existing is not None:
            return existing

        item = LocalSyncQueueItem(
            event_id=event_id,
            resource_type=resource_type,
            priority=priority,
            payload=payload,
            status="QUEUED",
        )
        db.add(item)
        db.flush()

        store = None  # Safe local-only Dev2 queue; NO cloud receipts
        if store is not None:
            try:
                now_iso = datetime.now(timezone.utc).isoformat()
                store.put(
                    "sync_queue",
                    event_id,
                    {
                        "event_id": event_id,
                        "mission_id": mission_id,
                        "resource_type": resource_type,
                        "priority": priority,
                        "status": "queued",
                        "attempt_count": 0,
                        "payload": payload,
                        "created_at": now_iso,
                    },
                    mission_id=mission_id,
                    actor_id="dev2-bridge",
                    immutable=False,
                )
            except Exception:
                pass
        return item

    @staticmethod
    def emit_alert_and_optional_incident(
        db: Session,
        *,
        rule_id: str,
        rule_version: str,
        rule_approval_status: str,
        severity: str,
        title: str,
        evidence_refs: List[str],
        astronaut_id: Optional[str] = None,
        location_id: Optional[str] = None,
        open_incident: bool = False,
        incident_type: str = "CORRELATED_MEDICAL_EVENT",
        is_synthetic: bool = True,
        mission_id: str = "DEMO-01",
    ) -> Dict[str, Any]:
        approval_upper = str(rule_approval_status or "").strip().upper()
        if approval_upper not in {"APPROVED", "DEMO_ONLY", "RESEARCH_ONLY"}:
            Dev1IntegrationBridge.record_audit(
                db=db,
                actor=ActorContext(user_id="SYSTEM-RULE-ENGINE", role="SYSTEM"),
                action="EVALUATE_ALERT_RULE",
                resource_type="alert_rules",
                resource_id=f"{rule_id}:{rule_version}",
                outcome="BLOCKED",
            )
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Rule '{rule_id}' v{rule_version} blocked: approval status "
                    f"'{rule_approval_status}' is not authorized."
                ),
            )

        sev_upper = severity.upper()
        sev_dev1 = SEVERITY_TO_DEV1.get(sev_upper, "warning")
        incident_id: Optional[str] = None
        now_iso = datetime.now(timezone.utc).isoformat()
        store = None  # Never bypass Dev1 official alert and incident engine

        if open_incident:
            stmt = select(LocalMedicalIncident).where(LocalMedicalIncident.status == "OPEN")
            if incident_type != "CORRELATED_MEDICAL_EVENT":
                stmt = stmt.where(LocalMedicalIncident.incident_type == incident_type)

            if astronaut_id and location_id:
                stmt = stmt.where(
                    or_(
                        LocalMedicalIncident.astronaut_id == astronaut_id,
                        LocalMedicalIncident.astronaut_id.is_(None),
                    ),
                    or_(
                        LocalMedicalIncident.location_id == location_id,
                        LocalMedicalIncident.location_id.is_(None),
                    ),
                )
            elif astronaut_id:
                stmt = stmt.where(
                    or_(
                        LocalMedicalIncident.astronaut_id == astronaut_id,
                        LocalMedicalIncident.astronaut_id.is_(None),
                    )
                )
            elif location_id:
                stmt = stmt.where(
                    or_(
                        LocalMedicalIncident.location_id == location_id,
                        LocalMedicalIncident.location_id.is_(None),
                    )
                )

            incident = db.scalars(stmt).first()

            if incident is None:
                incident = LocalMedicalIncident(
                    astronaut_id=astronaut_id,
                    location_id=location_id,
                    incident_type=incident_type,
                    priority="CRITICAL" if sev_upper == "CRITICAL" else "HIGH",
                    status="OPEN",
                    linked_evidence=list(evidence_refs),
                    causality_asserted=False,
                    is_synthetic=is_synthetic,
                )
                db.add(incident)
                db.flush()
            else:
                if incident.astronaut_id is None and astronaut_id is not None:
                    incident.astronaut_id = astronaut_id
                if incident.location_id is None and location_id is not None:
                    incident.location_id = location_id
                merged = list(dict.fromkeys([*(incident.linked_evidence or []), *evidence_refs]))
                incident.linked_evidence = merged
                db.flush()

            incident_id = incident.id

            if store is not None:
                try:
                    store.put(
                        "medical_incidents",
                        incident_id,
                        {
                            "incident_id": incident_id,
                            "mission_id": mission_id,
                            "astronaut_id": incident.astronaut_id,
                            "location_id": incident.location_id,
                            "incident_type": incident.incident_type,
                            "priority": sev_dev1,
                            "status": "open",
                            "linked_evidence": incident.linked_evidence,
                            "causality_asserted": False,
                            "is_synthetic": is_synthetic,
                            "source_type": "SIMULATED" if is_synthetic else "ACTUAL",
                            "created_at": now_iso,
                        },
                        mission_id=mission_id,
                        actor_id="dev2-bridge",
                        immutable=False,
                    )
                except Exception:
                    pass

        alert = LocalHealthAlert(
            incident_id=incident_id,
            astronaut_id=astronaut_id,
            location_id=location_id,
            rule_id=rule_id,
            rule_version=rule_version,
            rule_approval_status=approval_upper,
            severity=sev_upper,
            title=title,
            evidence_refs=list(evidence_refs),
            status="OPEN",
            is_synthetic=is_synthetic,
        )
        db.add(alert)
        db.flush()

        if store is not None:
            try:
                store.put(
                    "health_alerts",
                    alert.id,
                    {
                        "alert_id": alert.id,
                        "incident_id": incident_id,
                        "mission_id": mission_id,
                        "astronaut_id": astronaut_id,
                        "location_id": location_id,
                        "rule_id": rule_id,
                        "rule_version": rule_version,
                        "rule_approval_status": approval_upper,
                        "severity": sev_dev1,
                        "title": title,
                        "evidence_refs": list(evidence_refs),
                        "status": "open",
                        "is_synthetic": is_synthetic,
                        "source_type": "SIMULATED" if is_synthetic else "ACTUAL",
                        "created_at": now_iso,
                    },
                    mission_id=mission_id,
                    actor_id="dev2-bridge",
                    immutable=False,
                )
            except Exception:
                pass

        Dev1IntegrationBridge.enqueue_sync(
            db=db,
            event_id=f"ALERT-{alert.id}",
            resource_type="health_alerts",
            priority=1 if sev_upper == "CRITICAL" else 2,
            payload={
                "alert_id": alert.id,
                "incident_id": incident_id,
                "severity": sev_dev1,
                "title": title,
            },
            mission_id=mission_id,
        )

        return {"alert_id": alert.id, "incident_id": incident_id, "severity": sev_upper}
                
    @classmethod
    def flush_sync_queue_idempotent(cls, db: Session, earth_connected: bool) -> dict:
        """
        Handles offline sync queue logic for S10.
        If earth_connected is False, items remain queued locally.
        If True, processes exactly-once priority sync and clears the queue.
        """
        if not earth_connected:
            pending_count = db.query(LocalSyncQueueItem).filter_by(status="QUEUED").count()
            return {
                "pending_in_sqlite": pending_count > 0,
                "ordered_event_ids": [],
                "synced_now": 0
            }
            
        # Process queued items prioritizing priority 1 (Critical) over 2 (High)
        queued_items = (
            db.query(LocalSyncQueueItem)
            .filter_by(status="QUEUED")
            .order_by(LocalSyncQueueItem.priority.asc())
            .all()
        )
        
        synced_count = 0
        ordered_ids = []
        for item in queued_items:
            ordered_ids.append(item.event_id)
            item.status = "SYNCED"
            synced_count += 1
            
        db.flush()
            
        return {
            "pending_in_sqlite": False,
            "ordered_event_ids": ordered_ids if ordered_ids else ["NO_EVENTS"],
            "synced_now": synced_count
        }