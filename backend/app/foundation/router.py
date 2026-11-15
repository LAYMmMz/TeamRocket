from datetime import datetime, timezone
from inspect import Parameter, Signature, signature
from fastapi import APIRouter, Depends, Query
from app.auth.dependencies import require
from app.core.dependencies import get_store
from app.core.errors import AppError
from app.foundation.models import (
    AstronautWrite, CrewAssignment, DeviceAssignment,
    DeviceWrite, MissionWrite
)

router = APIRouter(tags=["foundation"])
read_access = Depends(require("foundation:read"))
write_access = Depends(require("foundation:manage"))
database = Depends(get_store)

def _record(store, kind, record_id):
    item = store.get(kind, record_id)
    if item is None or item.get("archived"):
        raise AppError(404, "not_found", "Not found")
    return item

def _policy(principal, data):
    if principal._environment == "production" and data.get("is_synthetic"):
        principal.deny(
            "foundation:synthetic_production_write",
            mission_id=data.get("mission_id"),
        )

def _source(store, mission_id, synthetic):
    mission = _record(store, "missions", mission_id)
    if mission["is_synthetic"] != synthetic:
        raise AppError(422, "synthetic_scope", "Synthetic scope mismatch")

def _unique(store, kind, record_id):
    if store.get(kind, record_id) is not None:
        raise AppError(409, "record_exists", "Record exists")

def _save(
    store, kind, record_id, payload,
    principal, mission_id, *, existing=None
):
    _policy(principal, payload)
    now = datetime.now(timezone.utc).isoformat()
    data = dict(
        payload,
        revision=existing["revision"] + 1 if existing else 1,
        created_at=existing["created_at"] if existing else now,
        updated_at=now,
        archived=False,
    )
    return store.put(
        kind, record_id, data, mission_id=mission_id,
        actor_id=principal.user_id, immutable=existing is None
    )

def _snapshot(store, kind, record_id, item, principal):
    store.put(
        "foundation_versions",
        f"{kind}:{record_id}:{item['revision']}",
        item, mission_id=item["mission_id"],
        actor_id=principal.user_id, enqueue=False,
    )

def _update(
    store, kind, record_id, data, principal, expected_revision
):
    principal.require_mission(
        _record(store, kind, record_id)["mission_id"]
    )
    _policy(principal, data)
    with store.transaction():
        old = _record(store, kind, record_id)
        mission = old["mission_id"]
        if data.get("mission_id") != mission:
            raise AppError(409, "mission_immutable", "Mission immutable")
        if kind != "missions":
            _source(store, mission, data["is_synthetic"])
        elif data["is_synthetic"] != old["is_synthetic"]:
            raise AppError(409, "synthetic_scope", "Synthetic scope mismatch")
        if expected_revision != old["revision"]:
            raise AppError(409, "revision_conflict", "Revision conflict")
        _snapshot(store, kind, record_id, old, principal)
        return _save(
            store, kind, record_id, data,
            principal, mission, existing=old
        )

def _archive(
    store, kind, record_id, principal, expected_revision
):
    old = _record(store, kind, record_id)
    principal.require_mission(old["mission_id"])
    _policy(principal, old)
    with store.transaction():
        old = _record(store, kind, record_id)
        if old["revision"] != expected_revision:
            raise AppError(409, "revision_conflict", "Revision conflict")
        _snapshot(store, kind, record_id, old, principal)
        old.update(
            archived=True,
            revision=old["revision"] + 1,
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        return store.put(
            kind, record_id, old,
            mission_id=old["mission_id"],
            actor_id=principal.user_id, immutable=False,
        )

def _list(store, kind, principal, mission=None):
    if mission is not None:
        principal.require_mission(mission)
    return [
        row for row in store.list(kind, mission_id=mission)
        if not row.get("archived")
        and (
            row["mission_id"] in principal.mission_ids
            or "*" in principal.mission_ids
        )
    ]

def crud(kind, model, key):
    def create(body: model, principal=write_access, store=database):
        principal.require_mission(body.mission_id)
        if kind == "missions":
            if principal.offline:
                principal.deny(
                    "foundation:create_mission_offline",
                    mission_id=body.mission_id,
                )
        else:
            _source(store, body.mission_id, body.is_synthetic)
        _unique(store, kind, getattr(body, key))
        return _save(
            store, kind, getattr(body, key),
            body.model_dump(mode="json"),
            principal, body.mission_id,
        )

    def collection(
        mission_id: str | None = None,
        principal=read_access, store=database
    ):
        return _list(store, kind, principal, mission_id)

    def missions(principal=read_access, store=database):
        return _list(store, kind, principal)

    def detail(principal=read_access, store=database, **path):
        if kind == "missions":
            principal.require_mission(path[key])
        item = _record(store, kind, path[key])
        principal.require_mission(item["mission_id"])
        return item

    def update(
        body: model,
        expected_revision: int = Query(ge=1),
        principal=write_access, store=database, **path
    ):
        if getattr(body, key) != path[key]:
            raise AppError(
                422, "identifier_mismatch",
                f"{key} must match the URL"
            )
        return _update(
            store, kind, path[key],
            body.model_dump(mode="json"),
            principal, expected_revision
        )

    def archive(
        expected_revision: int = Query(ge=1),
        principal=write_access, store=database, **path
    ):
        return _archive(
            store, kind, path[key], principal, expected_revision
        )

    for endpoint in [detail, update, archive]:
        parameters = [
            Parameter(
                key, Parameter.POSITIONAL_OR_KEYWORD,
                annotation=str
            )
        ]
        parameters += [
            parameter
            for parameter in signature(endpoint).parameters.values()
            if parameter.name != "path"
        ]
        endpoint.__signature__ = Signature(parameters)

    operations = [
        (create, f"/{kind}", "POST"),
        (
            missions if kind == "missions" else collection,
            f"/{kind}", "GET"
        ),
        (detail, f"/{kind}/{{{key}}}", "GET"),
        (update, f"/{kind}/{{{key}}}", "PUT"),
        (archive, f"/{kind}/{{{key}}}", "DELETE"),
    ]
    for endpoint, route, method in operations:
        router.add_api_route(
            route, endpoint, methods=[method],
            name=f"{kind}_{endpoint.__name__}",
            status_code=201 if method == "POST" else 200,
        )

for kind, model, key in [
    ("missions", MissionWrite, "mission_id"),
    ("astronauts", AstronautWrite, "astronaut_id"),
    ("devices", DeviceWrite, "device_id"),
]:
    crud(kind, model, key)

@router.get("/roles")
def roles(principal=read_access):
    return {
        "roles": [
            "admin", "flight_surgeon", "crew",
            "mission_control", "researcher"
        ],
        "status": "provisional_pending_db_team_mapping",
        "source_type": "SIMULATED",
        "is_synthetic": True,
    }

@router.post("/missions/{mission_id}/crew", status_code=201)
def assign_crew(
    mission_id: str, body: CrewAssignment,
    principal=write_access, store=database
):
    principal.require_mission(mission_id)
    _record(store, "missions", mission_id)
    if _record(store, "astronauts", body.astronaut_id)["mission_id"] != mission_id:
        raise AppError(409, "foreign_key_scope", "Foreign key scope mismatch")
    _unique(store, "mission_crew", body.assignment_id)
    _source(store, mission_id, body.is_synthetic)
    data = dict(body.model_dump(mode="json"), mission_id=mission_id)
    return _save(
        store, "mission_crew", body.assignment_id,
        data, principal, mission_id
    )

@router.get("/missions/{mission_id}/crew")
def list_crew(
    mission_id: str, principal=read_access, store=database
):
    principal.require_mission(mission_id)
    _record(store, "missions", mission_id)
    return _list(store, "mission_crew", principal, mission_id)

@router.post("/devices/{device_id}/assignments", status_code=201)
def assign_device(
    device_id: str, body: DeviceAssignment,
    principal=write_access, store=database
):
    mission = _record(store, "devices", device_id)["mission_id"]
    principal.require_mission(mission)
    if _record(store, "astronauts", body.astronaut_id)["mission_id"] != mission:
        raise AppError(409, "foreign_key_scope", "Foreign key scope mismatch")
    _source(store, mission, body.is_synthetic)
    _unique(store, "device_assignments", body.assignment_id)
    data = dict(
        body.model_dump(mode="json"),
        mission_id=mission, device_id=device_id
    )
    return _save(
        store, "device_assignments", body.assignment_id,
        data, principal, mission
    )

@router.get("/devices/{device_id}/assignments")
def device_assignments(
    device_id: str, principal=read_access, store=database
):
    mission = _record(store, "devices", device_id)["mission_id"]
    principal.require_mission(mission)
    return [
        row for row in _list(
            store, "device_assignments", principal, mission
        )
        if row["device_id"] == device_id
    ]
