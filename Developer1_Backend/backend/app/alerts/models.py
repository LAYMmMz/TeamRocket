from enum import Enum
from typing import Any, Literal
from pydantic import (
    AwareDatetime, BaseModel, ConfigDict, Field,
    FiniteFloat, model_validator
)

class RuleMode(str, Enum):
    OPERATIONAL = "OPERATIONAL"
    DEMO = "DEMO"
    RESEARCH = "RESEARCH"

class Rule(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    rule_id: str = Field(min_length=1, max_length=128)
    version: int = Field(ge=1)
    mission_id: str = Field(min_length=1, max_length=128)
    metric: str = Field(min_length=1, max_length=80)
    operator: Literal["gt", "ge", "lt", "le", "eq", "unavailable"]
    threshold: FiniteFloat | None = None
    unit: str | None = Field(
        default=None, min_length=1, max_length=48
    )
    severity: Literal[
        "information", "advisory", "warning",
        "critical", "data-unavailable"
    ]
    mode: RuleMode
    verification: Literal["VERIFIED", "UNVERIFIED", "REJECTED"]
    approval: Literal["APPROVED", "PENDING", "REJECTED"]
    approved_by: str | None = Field(default=None, max_length=128)
    valid_from: AwareDatetime
    valid_until: AwareDatetime
    source_revision: str = Field(min_length=1, max_length=128)
    source_reference: str = Field(min_length=1, max_length=2048)
    required_context: dict[str, Any] = Field(default_factory=dict)
    averaging_window_seconds: int | None = Field(
        default=None, gt=0, le=31536000
    )
    max_evidence_age_seconds: int = Field(
        default=3600, gt=0, le=31536000
    )
    correlation_key: str | None = Field(
        default=None, min_length=1, max_length=128
    )
    correlation_window_seconds: int = Field(
        default=3600, gt=0, le=86400
    )

    @model_validator(mode="after")
    def coherent_dates(self):
        if self.operator != "unavailable" and (
            self.threshold is None or not self.unit
        ):
            raise ValueError("Comparison requires threshold and unit")
        if (
            self.operator == "unavailable"
            and self.severity != "data-unavailable"
        ):
            raise ValueError(
                "Unavailable rules require data-unavailable severity"
            )
        if self.valid_until <= self.valid_from:
            raise ValueError("valid_until must follow valid_from")
        if self.approval == "APPROVED" and not self.approved_by:
            raise ValueError("approved_by is required")
        return self

    @property
    def storage_id(self):
        return (
            f"{len(self.mission_id)}:{self.mission_id}:"
            f"{len(self.rule_id)}:{self.rule_id}:{self.version}"
        )
