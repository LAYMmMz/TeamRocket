from typing import Literal
from pydantic import (
    AwareDatetime, BaseModel, ConfigDict, Field, model_validator
)

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

class Provenance(StrictModel):
    source_title: str = Field(min_length=1)
    source_revision: str = Field(min_length=1)
    source_uri: str | None = None
    verified_by: str | None = None
    verified_at: AwareDatetime | None = None
    approved_by: str | None = None
    approved_at: AwareDatetime | None = None

class Branch(StrictModel):
    option_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    next_step_order: int = Field(ge=1)

class ProcedureStep(StrictModel):
    order: int = Field(ge=1)
    title: str = Field(min_length=1)
    instruction: str = Field(min_length=1)
    branches: list[Branch] = Field(default_factory=list)

class Procedure(StrictModel):
    procedure_id: str = Field(
        min_length=1, pattern=r"^[A-Za-z0-9_-]+$"
    )
    version: int = Field(ge=1)
    mission_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    mode: Literal["OPERATIONAL", "DEMO", "RESEARCH"]
    source_type: Literal["REAL", "SIMULATED", "RESEARCH"]
    is_synthetic: bool
    approval_state: Literal["draft", "approved", "retired"]
    provenance: Provenance
    valid_from: AwareDatetime
    expires_at: AwareDatetime
    steps: list[ProcedureStep] = Field(min_length=1)

    @model_validator(mode="after")
    def consistency(self):
        if self.expires_at <= self.valid_from:
            raise ValueError("expires_at must follow valid_from")
        if self.is_synthetic != (self.source_type == "SIMULATED"):
            raise ValueError("Source and synthetic flags disagree")
        if self.mode == "DEMO" and not self.is_synthetic:
            raise ValueError("DEMO procedures must be SIMULATED")
        if self.mode == "OPERATIONAL" and self.source_type != "REAL":
            raise ValueError("Operational procedures require REAL sources")
        if self.mode == "RESEARCH" and self.source_type != "RESEARCH":
            raise ValueError("Research procedures require RESEARCH sources")

        orders = [step.order for step in self.steps]
        if orders != list(range(1, len(self.steps) + 1)):
            raise ValueError("Steps must be ordered from 1")
        for step in self.steps:
            ids = [branch.option_id for branch in step.branches]
            if len(set(ids)) != len(ids):
                raise ValueError("Branch IDs must be unique")
            for branch in step.branches:
                if (
                    branch.next_step_order not in orders
                    or branch.next_step_order <= step.order
                ):
                    raise ValueError(
                        "Branches must refer to a later existing step"
                    )
        return self

class Acknowledgment(StrictModel):
    event_id: str = Field(min_length=1)
    execution_id: str = Field(min_length=1)
    step_order: int = Field(ge=1)
    selected_option_id: str | None = None
    acknowledged_at: AwareDatetime
    operational: bool = True
