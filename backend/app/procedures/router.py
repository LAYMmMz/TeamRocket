from fastapi import APIRouter, Depends
from app.auth.dependencies import Principal, require
from app.core.dependencies import get_settings, get_store
from app.core.errors import AppError
from app.procedures.models import Acknowledgment, Procedure
from app.procedures.service import (
    acknowledge, check_access, get_procedure,
    neutral_guidance, save_procedure
)

router = APIRouter(prefix="/procedures", tags=["procedures"])

@router.get("/guidance")
def guidance(
    principal: Principal = Depends(require("procedures:read")),
    settings=Depends(get_settings),
):
    if settings.environment not in {"development", "test"}:
        raise AppError(403, "demo_disabled", "Demo disabled")
    return neutral_guidance()

@router.post("", status_code=201)
def create(
    body: Procedure,
    principal: Principal = Depends(require("procedures:manage")),
    store=Depends(get_store),
    settings=Depends(get_settings),
):
    principal.require_mission(body.mission_id)
    if principal.offline and body.mode == "OPERATIONAL":
        principal.deny(
            "procedures:offline_approval",
            mission_id=body.mission_id
        )
    return save_procedure(
        body, store, settings, principal.user_id
    )

@router.get("")
def listing(
    mission_id: str,
    principal: Principal = Depends(require("procedures:read")),
    store=Depends(get_store),
    settings=Depends(get_settings),
):
    principal.require_mission(mission_id)
    summaries = []
    for row in store.list("procedure", mission_id=mission_id):
        summary = {
            key: value for key, value in row.items()
            if key != "steps"
        }
        try:
            check_access(
                row, settings, operational=True, store=store
            )
            summary.update(
                operational_available=True,
                unavailable_reason=None,
            )
        except AppError as exc:
            summary.update(
                operational_available=False,
                unavailable_reason=exc.code,
            )
        summary["label"] = (
            "SIMULATED" if row["is_synthetic"]
            else (
                "APPROVED_OPERATIONAL"
                if summary["operational_available"]
                else "NON_OPERATIONAL_REVIEW"
            )
        )
        summaries.append(summary)
    return {"items": summaries}

@router.get("/{procedure_id}/versions/{version}")
def read(
    procedure_id: str,
    version: int,
    operational: bool = True,
    principal: Principal = Depends(require("procedures:read")),
    store=Depends(get_store),
    settings=Depends(get_settings),
):
    procedure = get_procedure(store, procedure_id, version)
    principal.require_mission(procedure.mission_id)
    try:
        check_access(
            procedure, settings,
            operational=operational, store=store
        )
    except AppError:
        store.audit(
            "procedure_access_denied", principal.user_id,
            mission_id=procedure.mission_id,
            record_id=procedure_id,
            details={
                "version": version,
                "operational": operational
            },
        )
        raise
    return procedure.model_dump(mode="json") | {
        "operational": operational,
        "label": (
            "SIMULATED" if procedure.is_synthetic
            else (
                "APPROVED_OPERATIONAL"
                if operational else "NON_OPERATIONAL_REVIEW"
            )
        ),
    }

@router.post(
    "/{procedure_id}/versions/{version}/acknowledgments",
    status_code=201,
)
def ack(
    procedure_id: str,
    version: int,
    body: Acknowledgment,
    principal: Principal = Depends(require("procedures:read")),
    store=Depends(get_store),
    settings=Depends(get_settings),
):
    procedure = get_procedure(store, procedure_id, version)
    principal.require_mission(procedure.mission_id)
    return acknowledge(
        procedure, body, store, settings, principal.user_id
    )
