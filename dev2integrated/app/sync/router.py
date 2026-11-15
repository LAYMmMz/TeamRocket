from fastapi import APIRouter, Depends, Request
from app.auth.dependencies import require
from app.core.dependencies import get_store
from app.core.errors import AppError

router = APIRouter(prefix="/sync", tags=["Offline sync"])

def _missions(principal):
    if "*" in principal.mission_ids:
        return None
    for mission_id in principal.mission_ids:
        principal.require_mission(mission_id)
    return list(principal.mission_ids)

@router.get("/status")
def status(
    principal=Depends(require("sync:manage")),
    store=Depends(get_store),
):
    return store.queue_status(mission_ids=_missions(principal))

@router.post("/run")
def run(
    request: Request,
    principal=Depends(require("sync:manage")),
    store=Depends(get_store),
):
    result = request.app.state.sync_worker.run_once(
        mission_ids=_missions(principal)
    )
    store.audit(
        "sync.run", principal.user_id,
        details={
            "missions": _missions(principal),
            "delivered": result["delivered"],
            "failed": result["failed"],
        },
    )
    return result

@router.get("/receipts/{kind}/{record_id}")
def receipt(
    kind: str,
    record_id: str,
    principal=Depends(require("sync:manage")),
    store=Depends(get_store),
):
    record = store.get(kind, record_id)
    if record is None:
        raise AppError(
            404, "record_not_found", "Local record not found"
        )
    mission_id = record.get("mission_id")
    if mission_id:
        principal.require_mission(mission_id)
    elif "*" not in principal.mission_ids:
        principal.deny("sync:global_receipt")
    value = store.receipt(kind, record_id)
    if value is None:
        raise AppError(
            404, "receipt_pending", "Cloud receipt pending"
        )
    return value
