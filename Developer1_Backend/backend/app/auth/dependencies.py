from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
from typing import Any

import jwt
from fastapi import Depends, Request
from fastapi.security import (
    HTTPAuthorizationCredentials, HTTPBearer
)

from app.core.errors import AppError

ROLE_PERMISSIONS = {
    "admin": frozenset({"*"}),
    "flight_surgeon": frozenset({
        "measurements:write", "measurements:read",
        "rules:manage", "alerts:read",
        "incidents:write", "incidents:read",
        "procedures:manage", "procedures:read",
        "inventory:manage", "inventory:read",
        "foundation:read", "sync:manage", "audit:read",
        "attachments:write", "attachments:read",
        "imports:write", "quality:read",
    }),
    "crew": frozenset({
        "measurements:write", "measurements:read",
        "alerts:read", "incidents:read", "procedures:read",
        "inventory:read", "foundation:read",
        "attachments:write", "attachments:read",
    }),
    "mission_control": frozenset({
        "alerts:read", "incidents:read", "procedures:read",
        "inventory:read", "foundation:read", "sync:manage",
    }),
    "researcher": frozenset({"foundation:read"}),
}

_bearer = HTTPBearer(auto_error=False)

def _utc_now():
    return datetime.now(timezone.utc)

def _timestamp(value):
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValueError("JWT timestamp must be numeric")
    return datetime.fromtimestamp(value, timezone.utc)

@dataclass
class Principal:
    user_id: str
    roles: list[str]
    mission_ids: list[str]
    offline: bool = False
    permissions: frozenset[str] = field(default_factory=frozenset)
    expires_at: datetime | None = None
    grant_id: str | None = None
    _store: Any = field(default=None, repr=False)
    _environment: str = field(default="development", repr=False)

    def deny(self, action, *, mission_id=None):
        if self._store is not None:
            self._store.audit(
                "authorization.denied", self.user_id,
                mission_id=mission_id,
                details={
                    "permission": action, "offline": self.offline
                },
            )
        raise AppError(403, "forbidden", "Forbidden")

    def require_mission(self, mission_id):
        if (
            mission_id not in self.mission_ids
            and "*" not in self.mission_ids
        ):
            self.deny("mission:access", mission_id=mission_id)
        if self.offline and self._store is not None:
            cached = self._store.get("missions", mission_id)
            if cached is None or cached.get("archived", False):
                self.deny(
                    "offline:uncached_mission", mission_id=mission_id
                )

    def allows(self, permission):
        return "*" in self.permissions or permission in self.permissions

def permissions_for(roles):
    return frozenset().union(
        *(ROLE_PERMISSIONS[role] for role in roles)
    )

def _trusted_metadata(claims):
    metadata = claims.get("app_metadata")
    if not isinstance(metadata, dict):
        raise ValueError("Missing trusted app metadata")
    roles = metadata.get("roles")
    missions = metadata.get("mission_ids")
    if (
        not isinstance(roles, list) or not roles
        or any(
            not isinstance(role, str) or role not in ROLE_PERMISSIONS
            for role in roles
        )
    ):
        raise ValueError("Invalid trusted role mapping")
    if (
        not isinstance(missions, list) or not missions
        or any(
            not isinstance(mission, str)
            or not mission.strip() or len(mission) > 128
            for mission in missions
        )
    ):
        raise ValueError("Missing mission scope")
    if "*" in missions and "admin" not in roles:
        raise ValueError("Wildcard mission scope requires admin")
    return sorted(set(roles)), sorted(set(missions))

@lru_cache(maxsize=8)
def _jwk_client(url):
    return jwt.PyJWKClient(
        url, cache_jwk_set=True, lifespan=300, timeout=5
    )

def _verify_online(token, settings):
    algorithm = jwt.get_unverified_header(token).get("alg")
    if (
        algorithm == "HS256"
        and settings.environment in {"development", "test"}
        and settings.dev_auth_secret
    ):
        return jwt.decode(
            token, settings.dev_auth_secret, algorithms=["HS256"],
            issuer="developer1-local", audience="authenticated",
            options={
                "require": ["exp", "iat", "sub", "iss", "aud"]
            },
        )
    if algorithm not in {"RS256", "ES256"}:
        raise ValueError("Unsupported signing algorithm")
    if not settings.auth_issuer or not settings.auth_jwks_url:
        raise ValueError("Online identity provider not configured")
    if not settings.auth_jwks_url.startswith("https://"):
        raise ValueError("JWKS endpoint requires HTTPS")
    signing_key = _jwk_client(
        settings.auth_jwks_url
    ).get_signing_key_from_jwt(token).key
    return jwt.decode(
        token, signing_key, algorithms=["RS256", "ES256"],
        issuer=settings.auth_issuer,
        audience=settings.auth_audience,
        options={"require": ["exp", "iat", "sub", "iss", "aud"]},
    )

def _verify_offline(token, settings, store):
    if not settings.offline_grant_secret:
        raise ValueError("Offline authorization not configured")
    claims = jwt.decode(
        token, settings.offline_grant_secret,
        algorithms=["HS256"],
        issuer="developer1-onboard",
        audience="onboard-offline",
        options={
            "require": [
                "exp", "iat", "nbf", "sub", "iss", "aud", "jti"
            ]
        },
    )
    issued = _timestamp(claims["iat"])
    expires = _timestamp(claims["exp"])
    maximum = settings.offline_grant_max_hours * 3600
    if (
        expires <= issued
        or (expires - issued).total_seconds() > maximum
    ):
        raise ValueError("Offline lifetime exceeds configured bound")
    jti = claims["jti"]
    if not isinstance(jti, str):
        raise ValueError("Invalid grant identifier")
    cached = store.get("offline_grants", jti)
    if (
        not cached
        or cached.get("revoked")
        or cached.get("user_id") != claims["sub"]
        or cached.get("token_sha256")
        != hashlib.sha256(token.encode()).hexdigest()
    ):
        raise ValueError("Grant not cached or revoked")
    return claims, jti

def authenticate_token(token, settings, store):
    try:
        header = jwt.get_unverified_header(token)
        offline = header.get("typ") == "offline-grant+jwt"
        grant_id = None
        if offline:
            claims, grant_id = _verify_offline(
                token, settings, store
            )
        else:
            claims = _verify_online(token, settings)

        subject = claims.get("sub")
        if (
            not isinstance(subject, str)
            or not subject.strip() or len(subject) > 128
        ):
            raise ValueError("Invalid subject")

        roles, missions = _trusted_metadata(claims)
        permissions = permissions_for(roles)
        if offline:
            granted = claims.get("permissions")
            if (
                not isinstance(granted, list)
                or any(not isinstance(p, str) for p in granted)
            ):
                raise ValueError("Invalid offline permission snapshot")
            permissions = (
                frozenset(granted)
                if "*" in permissions
                else permissions.intersection(granted)
            )

        return Principal(
            user_id=subject,
            roles=roles,
            mission_ids=missions,
            offline=offline,
            permissions=permissions,
            expires_at=_timestamp(claims["exp"]),
            grant_id=grant_id,
            _store=store,
            _environment=settings.environment,
        )
    except (
        jwt.PyJWTError, ValueError, TypeError,
        KeyError, OverflowError
    ) as exc:
        store.audit(
            "authentication.denied", "anonymous",
            details={"reason": type(exc).__name__},
        )
        raise AppError(
            401, "invalid_session", "Invalid or expired session"
        ) from None

async def current_principal(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None
    = Depends(_bearer),
):
    if credentials is None or credentials.scheme.lower() != "bearer":
        request.app.state.store.audit(
            "authentication.denied", "anonymous",
            details={"reason": "missing_bearer"},
        )
        raise AppError(
            401, "authentication_required", "Bearer session required"
        )
    principal = authenticate_token(
        credentials.credentials,
        request.app.state.settings,
        request.app.state.store,
    )
    request.state.principal = principal
    return principal

def require(permission):
    async def permission_dependency(
        principal: Principal = Depends(current_principal),
    ):
        if not principal.allows(permission):
            principal.deny(permission)
        return principal
    return permission_dependency

def issue_development_token(
    settings, user_id, roles, mission_ids, ttl_minutes=60
):
    if (
        settings.environment not in {"development", "test"}
        or not settings.dev_auth_secret
    ):
        raise ValueError("Development token issuance is disabled")
    if not 1 <= ttl_minutes <= 120:
        raise ValueError("Development tokens expire within two hours")
    now = int(_utc_now().timestamp())
    claims = {
        "sub": user_id,
        "iss": "developer1-local",
        "aud": "authenticated",
        "iat": now,
        "exp": now + ttl_minutes * 60,
        "app_metadata": {
            "roles": roles, "mission_ids": mission_ids
        },
    }
    _trusted_metadata(claims)
    return jwt.encode(
        claims, settings.dev_auth_secret, algorithm="HS256"
    )
