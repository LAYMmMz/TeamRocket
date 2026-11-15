from typing import Literal
from pydantic import AwareDatetime, Field, model_validator
from app.procedures.models import StrictModel

class CatalogEntry(StrictModel):
    catalog_id: str = Field(min_length=1)
    version: int = Field(ge=1)
    code: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    source_name: str = Field(min_length=1)
    source_revision: str = Field(min_length=1)
    source_uri: str | None = None
    source_type: Literal["REAL", "SIMULATED"]
    is_synthetic: bool
    license_reference: str | None = None
    verified_by: str | None = None
    verified_at: AwareDatetime | None = None

    @model_validator(mode="after")
    def source_consistency(self):
        if self.is_synthetic != (self.source_type == "SIMULATED"):
            raise ValueError("Source and synthetic flags disagree")
        if not self.is_synthetic and not all([
            self.license_reference, self.verified_by,
            self.verified_at, self.source_uri
        ]):
            raise ValueError(
                "Official imports require license, source and verification"
            )
        if self.is_synthetic and self.source_name != "DEMO":
            raise ValueError("Synthetic catalogs must use DEMO source")
        return self

class CatalogImport(StrictModel):
    entries: list[CatalogEntry] = Field(
        min_length=1, max_length=1000
    )

class InventoryLot(StrictModel):
    lot_id: str = Field(min_length=1)
    mission_id: str = Field(min_length=1)
    item_id: str = Field(min_length=1)
    item_name: str = Field(min_length=1)
    category: Literal[
        "medication", "antimicrobial", "equipment", "consumable"
    ]
    lot_number: str = Field(min_length=1)
    quantity: int = Field(ge=0)
    unit: str = Field(min_length=1)
    expires_at: AwareDatetime
    source_type: Literal["REAL", "SIMULATED"]
    is_synthetic: bool

    @model_validator(mode="after")
    def source_consistency(self):
        if self.is_synthetic != (self.source_type == "SIMULATED"):
            raise ValueError("Source and synthetic flags disagree")
        return self

class Administration(StrictModel):
    event_id: str = Field(min_length=1)
    mission_id: str = Field(min_length=1)
    astronaut_id: str = Field(min_length=1)
    lot_id: str = Field(min_length=1)
    clinician_selected_item_id: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    unit: str = Field(min_length=1)
    authorization_reference: str = Field(min_length=1)
    authorizing_clinician_id: str = Field(min_length=1)
    recorded_dose: str | None = None
    measured_at: AwareDatetime
    received_at: AwareDatetime
    source_type: Literal["REAL", "SIMULATED"]
    is_synthetic: bool
    quality: Literal["VALID", "SUSPECT", "INVALID", "MISSING", "STALE"]
    verification: Literal["VERIFIED", "UNVERIFIED", "REJECTED"]

    @model_validator(mode="after")
    def valid_metadata(self):
        if self.is_synthetic != (self.source_type == "SIMULATED"):
            raise ValueError("Source and synthetic flags disagree")
        if self.received_at < self.measured_at:
            raise ValueError("received_at precedes measured_at")
        return self

class Countermeasure(StrictModel):
    event_id: str = Field(min_length=1)
    mission_id: str = Field(min_length=1)
    astronaut_id: str = Field(min_length=1)
    kind: Literal["fluid", "compression", "medication", "other"]
    status: Literal["planned", "completed", "cancelled"]
    authorization_reference: str = Field(min_length=1)
    authorizing_clinician_id: str = Field(min_length=1)
    administration_event_id: str | None = None
    inventory_lot_id: str | None = None
    measured_observation_ids: list[str] = Field(default_factory=list)
    measured_at: AwareDatetime
    received_at: AwareDatetime
    source_type: Literal["REAL", "SIMULATED"]
    is_synthetic: bool
    quality: Literal["VALID", "SUSPECT", "INVALID", "MISSING", "STALE"]
    verification: Literal["VERIFIED", "UNVERIFIED", "REJECTED"]

    @model_validator(mode="after")
    def valid_metadata(self):
        if self.is_synthetic != (self.source_type == "SIMULATED"):
            raise ValueError("Source and synthetic flags disagree")
        if self.received_at < self.measured_at:
            raise ValueError("received_at precedes measured_at")
        if (
            self.kind == "medication"
            and self.status == "completed"
            and not self.administration_event_id
        ):
            raise ValueError(
                "Completed medication requires an administration link"
            )
        return self
