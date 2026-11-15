from datetime import datetime, timezone
from typing import Literal
from pydantic import (
    BaseModel, ConfigDict, AwareDatetime, model_validator
)

def utc_now():
    return datetime.now(timezone.utc)

class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

class Provenance(Contract):
    event_id: str
    source_type: Literal["REAL", "SIMULATED", "RESEARCH"]
    is_synthetic: bool
    measured_at: AwareDatetime
    quality: Literal["VALID", "SUSPECT", "INVALID", "MISSING", "STALE"]
    verification: Literal["VERIFIED", "UNVERIFIED", "REJECTED"]
    source_reference: str
    source_revision: str

    @model_validator(mode="after")
    def source_consistency(self):
        if self.source_type == "SIMULATED" and not self.is_synthetic:
            raise ValueError("SIMULATED evidence must be synthetic")
        if self.source_type == "REAL" and self.is_synthetic:
            raise ValueError("Synthetic evidence cannot be REAL")
        if not all([
            self.event_id.strip(),
            self.source_reference.strip(),
            self.source_revision.strip()
        ]):
            raise ValueError("Identity and provenance must not be blank")
        return self
