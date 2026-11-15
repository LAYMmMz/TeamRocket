from datetime import datetime, timezone
import hashlib
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, Field
import jwt

from app.auth.dependencies import Principal, current_principal
from app.core.errors import AppError

router = APIRouter(prefix="/auth", tags=["auth"])

class OfflineGrantRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mission_ids: list[str] = Field(min_length=1, max_length=20)
    hours: float = Field(gt=0, le=24)
    permissions: list[str] | None = None

class OfflineGrantResponse(BaseModel):
    grant_id: str
    token: str
    token_type: str = "bearer"
    expires_at: datetime
    mission_ids: list[str]
    permissions: list[str]
    offline: bool = True

@router.get("/session")
def session(
    principal: Annotated[Principal, Depends(current_principal)],
):
    return {
        "user_id": principal.user_id,
        "roles": principal.roles,
        "mission_ids": principal.mission_ids,
        "offline": principal.offline,
        "permissions": sorted(principal.permissions),
        "expires_at": principal.expires_at,
    }

@router.post(
    "/offline-grants",
    response_model=OfflineGrantResponse,
    status_code=201,
)
def create_offline_grant(
    body: OfflineGrantRequest,
    request: Request,
    principal: Annotated[Principal, Depends(current_principal)],
):
    if principal.offline:
        principal.deny("auth:extend_offline_grant")
    settings = request.app.state.settings
    store = request.app.state.store
    if not settings.offline_grant_secret:
        raise AppError(
            503, "offline_authorization_unconfigured",
            "Offline authorization unconfigured"
        )
    if body.hours > settings.offline_grant_max_hours:
        raise AppError(
            422, "grant_lifetime_exceeded", "Grant lifetime exceeded"
        )
    missions = sorted(set(body.mission_ids))
    if "*" in missions:
        raise AppError(
            422, "offline_scope_required", "Explicit scope required"
        )
    for mission_id in missions:
        principal.require_mission(mission_id)
        cached = store.get("missions", mission_id)
        if cached is None or cached.get("archived", False):
            raise AppError(
                409, "mission_not_cached", "Active mission not cached"
            )

    permissions = sorted(
        principal.permissions
        if body.permissions is None
        else set(body.permissions)
    )
    if not permissions or any(
        not principal.allows(permission)
        for permission in permissions
    ):
        principal.deny("auth:expand_permissions")

    grant_id = str(uuid4())
    now = int(datetime.now(timezone.utc).timestamp())
    expires = now + int(body.hours * 3600)
    claims = {
        "iss": "developer1-onboard",
        "aud": "onboard-offline",
        "sub": principal.user_id,
        "iat": now,
        "nbf": now,
        "exp": expires,
        "jti": grant_id,
        "app_metadata": {
            "roles": principal.roles,
            "mission_ids": missions,
        },
        "permissions": permissions,
    }
    token = jwt.encode(
        claims, settings.offline_grant_secret,
        algorithm="HS256",
        headers={"typ": "offline-grant+jwt"},
    )
    expires_at = datetime.fromtimestamp(expires, timezone.utc)
    store.put(
        "offline_grants", grant_id,
        {
            "grant_id": grant_id,
            "user_id": principal.user_id,
            "mission_ids": missions,
            "permissions": permissions,
            "expires_at": expires_at.isoformat(),
            "revoked": False,
            "token_sha256": hashlib.sha256(token.encode()).hexdigest(),
        },
        actor_id=principal.user_id,
        enqueue=False,
    )
    return OfflineGrantResponse(
        grant_id=grant_id,
        token=token,
        expires_at=expires_at,
        mission_ids=missions,
        permissions=permissions,
    )

@router.delete("/offline-grants/{grant_id}", status_code=204)
def revoke_offline_grant(
    grant_id: str,
    request: Request,
    principal: Annotated[Principal, Depends(current_principal)],
):
    if principal.offline:
        principal.deny("auth:revoke_offline_grant")
    store = request.app.state.store
    cached = store.get("offline_grants", grant_id)
    if cached is None:
        raise AppError(404, "grant_not_found", "Grant not found")
    if cached["user_id"] != principal.user_id and "admin" not in principal.roles:
        principal.deny("auth:revoke_other_grant")
    for mission_id in cached["mission_ids"]:
        principal.require_mission(mission_id)
    cached["revoked"] = True
    store.put(
        "offline_grants", grant_id, cached,
        actor_id=principal.user_id,
        enqueue=False, immutable=False,
    )
