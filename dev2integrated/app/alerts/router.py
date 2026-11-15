from fastapi import APIRouter, Depends
from app.alerts.models import Rule
from app.auth.dependencies import require
from app.core.dependencies import get_store
from app.core.errors import AppError

router = APIRouter(
    prefix="/alerts", tags=["alerts and versioned rules"]
)

@router.post("/rules", status_code=201, response_model=Rule)
def create_rule(
    rule: Rule,
    principal=Depends(require("rules:manage")),
    store=Depends(get_store),
):
    principal.require_mission(rule.mission_id)
    if principal.offline and rule.mode.value == "OPERATIONAL":
        store.audit(
            "access_denied", principal.user_id,
            mission_id=rule.mission_id,
            record_id=rule.storage_id,
            details={"reason": "offline_rule_approval_forbidden"},
        )
        raise AppError(
            403, "offline_rule_approval_forbidden",
            "Offline approval forbidden"
        )
    if store.get("alert_rule", rule.storage_id) is None and any(
        row["rule_id"] == rule.rule_id
        and row["version"] >= rule.version
        for row in store.list(
            "alert_rule", mission_id=rule.mission_id
        )
    ):
        raise AppError(
            409, "rule_version_conflict", "Rule version conflict"
        )
    return store.put(
        "alert_rule", rule.storage_id,
        rule.model_dump(mode="json"),
        mission_id=rule.mission_id,
        actor_id=principal.user_id,
    )

@router.get("/rules", response_model=list[Rule])
def list_rules(
    mission_id: str,
    principal=Depends(require("rules:manage")),
    store=Depends(get_store),
):
    principal.require_mission(mission_id)
    return store.list("alert_rule", mission_id=mission_id)

@router.get("")
def list_alerts(
    mission_id: str,
    principal=Depends(require("alerts:read")),
    store=Depends(get_store),
):
    principal.require_mission(mission_id)
    return {"items": store.list("health_alert", mission_id=mission_id)}

@router.get("/{event_id}")
def get_alert(
    event_id: str,
    principal=Depends(require("alerts:read")),
    store=Depends(get_store),
):
    record = store.get("health_alert", event_id)
    if record is None:
        raise AppError(404, "not_found", "Alert not found")
    principal.require_mission(record["mission_id"])
    return record
