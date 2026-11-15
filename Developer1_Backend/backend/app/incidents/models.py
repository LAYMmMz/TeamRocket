from typing import Literal
from pydantic import (
    AwareDatetime, BaseModel, ConfigDict, Field, model_validator
)

class SeriousSymptom(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: str = Field(min_length=1, max_length=128)
    mission_id: str = Field(min_length=1, max_length=128)
    astronaut_id: str = Field(min_length=1, max_length=128)
    symptom: str = Field(min_length=1, max_length=1000)
    severity: Literal["serious", "severe", "critical"]
    onset: AwareDatetime
    body_location: str = Field(min_length=1, max_length=128)
    source_type: Literal["REAL", "SIMULATED"]
    is_synthetic: bool
    measured_at: AwareDatetime
    received_at: AwareDatetime
    quality: Literal["VALID", "SUSPECT", "INVALID", "MISSING", "STALE"]
    verification: Literal["VERIFIED", "UNVERIFIED", "REJECTED"]

    @model_validator(mode="after")
    def source_consistent(self):
        if self.is_synthetic != (self.source_type == "SIMULATED"):
            raise ValueError("Source and synthetic flags disagree")
        if self.onset > self.measured_at or self.measured_at > self.received_at:
            raise ValueError("Symptom timestamps are out of order")
        return self

class IncidentEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: str = Field(min_length=1, max_length=128)
    kind: Literal["ACKNOWLEDGED", "CLOSED", "REOPENED", "NOTE"]
    note: str = Field(min_length=1, max_length=2000)
