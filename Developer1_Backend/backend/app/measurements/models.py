from typing import Any

from pydantic import Field, model_validator

from app.core.models import Provenance


class Measurement(Provenance):
    mission_id: str = Field(min_length=1, max_length=128)
    astronaut_id: str | None = Field(default=None, max_length=128)
    device_id: str | None = Field(default=None, max_length=128)
    metric: str = Field(min_length=1, max_length=80)
    value: float | None
    unit: str = Field(min_length=1, max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def missing_value(self):
        if self.value is None and self.quality != "MISSING":
            raise ValueError(
                "Only MISSING observations may have no value"
            )

        if self.quality == "MISSING" and self.value is not None:
            raise ValueError(
                "MISSING observations cannot include a value"
            )

        return self
    