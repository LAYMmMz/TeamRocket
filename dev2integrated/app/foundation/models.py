from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

def now_utc():
    return datetime.now(timezone.utc)

class FoundationModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid", str_strip_whitespace=True
    )
    source_type: Literal["REAL", "SIMULATED", "RESEARCH"] = "SIMULATED"
    is_synthetic: bool = True
    source_revision: str = Field(
        default="developer1-contract-v1", min_length=1, max_length=200
    )
    verification: Literal[
        "VERIFIED", "UNVERIFIED", "REJECTED"
    ] = "UNVERIFIED"
    source_reference: str = Field(
        default="local-foundation-contract",
        min_length=1, max_length=200
    )

    @model_validator(mode="after")
    def source_consistency(self):
        if self.source_type == "SIMULATED" and not self.is_synthetic:
            raise ValueError("SIMULATED records must be synthetic")
        if self.source_type == "REAL" and self.is_synthetic:
            raise ValueError("Synthetic records cannot be REAL")
        return self

class MissionWrite(FoundationModel):
    mission_id: str = Field(
        min_length=1, max_length=128,
        pattern=r"^[A-Za-z0-9_.:-]+$"
    )
    name: str = Field(min_length=1, max_length=200)
    starts_at: datetime | None = None
    ends_at: datetime | None = None

    @model_validator(mode="after")
    def interval(self):
        for stamp in [self.starts_at, self.ends_at]:
            if stamp is not None and stamp.tzinfo is None:
                raise ValueError("Mission timestamps require timezone")
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            raise ValueError("ends_at must follow starts_at")
        return self

class AstronautWrite(FoundationModel):
    astronaut_id: str = Field(
        min_length=1, max_length=128,
        pattern=r"^[A-Za-z0-9_.:-]+$"
    )
    mission_id: str = Field(min_length=1, max_length=128)
    display_name: str = Field(min_length=1, max_length=200)
    user_id: str | None = Field(default=None, max_length=128)

class DeviceWrite(FoundationModel):
    device_id: str = Field(
        min_length=1, max_length=128,
        pattern=r"^[A-Za-z0-9_.:-]+$"
    )
    mission_id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=200)
    device_type: str = Field(min_length=1, max_length=100)
    location: str = Field(min_length=1, max_length=200)
    calibration_reference: str | None = Field(
        default=None, max_length=200
    )

class CrewAssignment(FoundationModel):
    assignment_id: str = Field(
        default_factory=lambda: str(uuid4()),
        min_length=1, max_length=128
    )
    astronaut_id: str = Field(min_length=1, max_length=128)
    duty_role: str = Field(
        default="crew", min_length=1, max_length=100
    )

class DeviceAssignment(FoundationModel):
    assignment_id: str = Field(
        default_factory=lambda: str(uuid4()),
        min_length=1, max_length=128
    )
    astronaut_id: str = Field(min_length=1, max_length=128)
    starts_at: datetime = Field(default_factory=now_utc)
    ends_at: datetime | None = None

    @model_validator(mode="after")
    def interval(self):
        if self.starts_at.tzinfo is None or (
            self.ends_at and self.ends_at.tzinfo is None
        ):
            raise ValueError("Assignment timestamps require timezone")
        if self.ends_at is not None and self.ends_at <= self.starts_at:
            raise ValueError("ends_at must follow starts_at")
        return self
