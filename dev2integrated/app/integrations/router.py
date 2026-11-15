import base64
import binascii
import hashlib
from pathlib import PurePath
from typing import Any, Literal

from fastapi import APIRouter, Depends, Response
from pydantic import Field, model_validator

from app.auth.dependencies import require
from app.core.dependencies import get_settings, get_store
from app.core.errors import AppError
from app.core.models import Contract, Provenance, utc_now
from app.integrations.schema import inspect_handoff

router = APIRouter(tags=["audit and integrations"])

def persist_arrival(
    store, kind, record_id, payload, mission_id, actor_id
):
    conflict = None
    with store.transaction():
        existing = store.get(kind, record_id)
        payload["received_at"] = (
            existing["received_at"]
            if existing else utc_now().isoformat()
        )
        try:
            saved = store.put(
                kind, record_id, payload,
                mission_id=mission_id, actor_id=actor_id
            )
        except AppError as exc:
            if exc.status_code != 409:
                raise
            conflict = exc
    if conflict is not None:
        raise conflict
    return saved

class Attachment(Provenance):
    mission_id: str = Field(min_length=1)
    filename: str = Field(min_length=1, max_length=128)
    media_type: Literal[
        "application/pdf", "text/csv", "application/json",
        "image/png", "image/jpeg"
    ]
    content_base64: str = Field(max_length=14_000_000)

    @model_validator(mode="after")
    def safe_name(self):
        if (
            self.filename != PurePath(self.filename).name
            or any(
                character in self.filename
                for character in "\\\r\n\x00"
            )
            or self.filename in {".", ".."}
        ):
            raise ValueError("Filename cannot contain a path")
        return self

class ImportBatch(Contract):
    batch_id: str
    mission_id: str
    source_type: Literal["REAL", "SIMULATED", "RESEARCH"]
    is_synthetic: bool
    source_reference: str = Field(min_length=1)
    source_revision: str = Field(min_length=1)
    checksum_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    records_expected: int = Field(ge=0)
    purpose: Literal["clinical", "research_evidence", "simulation"]

    @model_validator(mode="after")
    def provenance(self):
        if self.source_type == "RESEARCH" and self.purpose != "research_evidence":
            raise ValueError("Research imports must remain separate")
        if (
            (self.source_type == "SIMULATED") != self.is_synthetic
            or (
                self.is_synthetic and self.purpose != "simulation"
            )
        ):
            raise ValueError("Simulation provenance mismatch")
        return self

class ResearchMetric(Provenance):
    mission_id: str
    metric: Literal["CHI", "TME", "QTL", "EVAC", "LOCL"]
    model_revision: str = Field(min_length=1)
    inputs: dict[str, Any]
    result: dict[str, Any]
    reviewer_status: Literal["PENDING", "REVIEWED", "REJECTED"]
    research_only: Literal[True] = True

@router.get("/schema/readiness")
def schema_readiness(
    principal=Depends(require("foundation:read")),
    settings=Depends(get_settings),
):
    return inspect_handoff(settings.schema_manifest_path)

@router.get("/audit")
def audit_log(
    mission_id: str,
    principal=Depends(require("audit:read")),
    store=Depends(get_store),
):
    principal.require_mission(mission_id)
    return {"items": store.list("audit", mission_id=mission_id)}

@router.post("/attachments", status_code=201)
def create_attachment(
    record: Attachment,
    principal=Depends(require("attachments:write")),
    store=Depends(get_store),
    settings=Depends(get_settings),
):
    principal.require_mission(record.mission_id)
    try:
        content = base64.b64decode(
            record.content_base64, validate=True
        )
    except (ValueError, binascii.Error):
        raise AppError(422, "invalid_file", "Invalid base64 file")

    if len(content) > settings.max_attachment_bytes:
        raise AppError(413, "file_too_large", "File too large")
    if settings.environment == "production" and record.is_synthetic:
        raise AppError(
            403, "synthetic_production_blocked",
            "Synthetic files blocked in production"
        )

    payload = record.model_dump(mode="json")
    payload.update(
        checksum_sha256=hashlib.sha256(content).hexdigest(),
        size_bytes=len(content),
    )
    stored = persist_arrival(
        store, "attachment", record.event_id,
        payload, record.mission_id, principal.user_id
    )
    return {
        key: value for key, value in stored.items()
        if key != "content_base64"
    }

@router.get("/attachments/{event_id}")
def get_attachment(
    event_id: str,
    principal=Depends(require("attachments:read")),
    store=Depends(get_store),
):
    record = store.get("attachment", event_id)
    if not record:
        raise AppError(404, "not_found", "Attachment not found")
    principal.require_mission(record["mission_id"])
    store.audit(
        "attachment_access", principal.user_id,
        mission_id=record["mission_id"], record_id=event_id
    )
    return Response(
        base64.b64decode(record["content_base64"]),
        media_type=record["media_type"],
        headers={
            "Content-Disposition": "attachment",
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "no-store",
        },
    )

@router.post("/import-batches", status_code=201)
def create_import_batch(
    record: ImportBatch,
    principal=Depends(require("imports:write")),
    store=Depends(get_store),
    settings=Depends(get_settings),
):
    principal.require_mission(record.mission_id)
    if settings.environment == "production" and record.is_synthetic:
        raise AppError(
            403, "synthetic_production_blocked",
            "Simulation import blocked in production"
        )
    return persist_arrival(
        store, "import_batch", record.batch_id,
        record.model_dump(mode="json"),
        record.mission_id, principal.user_id
    )

@router.post("/research-metrics", status_code=201)
def create_research_metric(
    record: ResearchMetric,
    principal=Depends(require("imports:write")),
    store=Depends(get_store),
):
    principal.require_mission(record.mission_id)
    if record.source_type != "RESEARCH":
        raise AppError(
            422, "research_only", "Research source label required"
        )
    return persist_arrival(
        store, "research_metric", record.event_id,
        record.model_dump(mode="json"),
        record.mission_id, principal.user_id
    )

@router.get("/data-quality")
def data_quality(
    mission_id: str,
    principal=Depends(require("quality:read")),
    store=Depends(get_store),
):
    principal.require_mission(mission_id)
    return {
        "quarantined": store.list(
            "quarantine", mission_id=mission_id
        ),
        "conflicts": store.list(
            "conflict", mission_id=mission_id
        ),
    }
