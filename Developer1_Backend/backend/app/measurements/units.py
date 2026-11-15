from datetime import datetime
import math

from app.core.errors import AppError
from app.measurements.models import Measurement


# Raw unit -> canonical unit, multiplier, offset.
UNITS = {
    "heart_rate": {
        "bpm": ("bpm", 1, 0),
    },
    "spo2": {
        "%": ("%", 1, 0),
    },
    "respiratory_rate": {
        "breaths/min": ("breaths/min", 1, 0),
    },
    "systolic_bp": {
        "mmHg": ("mmHg", 1, 0),
    },
    "diastolic_bp": {
        "mmHg": ("mmHg", 1, 0),
    },
    "temperature": {
        "Cel": ("Cel", 1, 0),
        "[degF]": ("Cel", 5 / 9, -32 * 5 / 9),
    },
    "ppco2": {
        "kPa": ("kPa", 1, 0),
        "mmHg": ("kPa", 0.133322387415, 0),
    },
    "ppo2": {
        "kPa": ("kPa", 1, 0),
        "mmHg": ("kPa", 0.133322387415, 0),
    },
    "pressure": {
        "kPa": ("kPa", 1, 0),
    },
    "noise": {
        "dB(A)": ("dB(A)", 1, 0),
    },
    "light": {
        "lux": ("lux", 1, 0),
    },
    "radiation_dose": {
        "mSv": ("mSv", 1, 0),
        "uSv": ("mSv", 0.001, 0),
        "Sv": ("mSv", 1000, 0),
    },
}


def validate_domain(record: Measurement) -> None:
    if (
        record.metric not in UNITS
        or record.unit not in UNITS[record.metric]
    ):
        raise AppError(
            422,
            "invalid_unit",
            "Unsupported metric/unit pair",
        )

    _, multiplier, offset = UNITS[record.metric][record.unit]

    if record.value is not None and not math.isfinite(
        record.value * multiplier + offset
    ):
        raise AppError(
            422,
            "normalization_overflow",
            "Normalization overflow",
        )

    required = set()

    if record.metric in {
        "ppco2", "ppo2", "pressure", "noise", "light"
    }:
        required |= {
            "zone",
            "averaging_window_seconds",
            "calibration_revision",
        }

    if record.metric == "noise":
        required.add("weighting")

        if record.metadata.get("weighting") != "A":
            raise AppError(
                422,
                "invalid_metadata",
                "dB(A) requires A weighting",
            )

    if record.metric == "radiation_dose":
        required |= {
            "interval_start",
            "interval_end",
            "dose_quantity",
            "location",
        }

        try:
            start = datetime.fromisoformat(
                str(
                    record.metadata.get("interval_start", "")
                ).replace("Z", "+00:00")
            )
            end = datetime.fromisoformat(
                str(
                    record.metadata.get("interval_end", "")
                ).replace("Z", "+00:00")
            )

            if (
                start.utcoffset() is None
                or end.utcoffset() is None
                or end <= start
            ):
                raise ValueError("Invalid interval")

        except (ValueError, TypeError) as exc:
            raise AppError(
                422,
                "invalid_interval",
                "Invalid dose interval",
            ) from exc

        if record.metadata.get("dose_quantity") not in {
            "effective", "equivalent"
        }:
            raise AppError(
                422,
                "invalid_dose_quantity",
                "Sv requires effective/equivalent dose provenance",
            )

    missing = required - record.metadata.keys()

    if missing:
        raise AppError(
            422,
            "missing_metadata",
            "Required metadata missing",
            sorted(missing),
        )

    for key in required & {
        "zone", "location", "calibration_revision"
    }:
        value = record.metadata[key]

        if not isinstance(value, str) or not value.strip():
            raise AppError(
                422,
                "invalid_metadata",
                "Empty metadata identifier",
            )

    if "averaging_window_seconds" in required:
        window = record.metadata["averaging_window_seconds"]

        if (
            isinstance(window, bool)
            or not isinstance(window, (int, float))
            or not math.isfinite(window)
            or window <= 0
        ):
            raise AppError(
                422,
                "invalid_window",
                "Invalid averaging window",
            )

    if record.value is not None:
        if record.value < 0 and record.metric != "temperature":
            raise AppError(
                422,
                "invalid_value",
                "Negative value invalid",
            )

        if record.metric == "spo2" and not 0 <= record.value <= 100:
            raise AppError(
                422,
                "invalid_value",
                "Percentage outside physical bounds",
            )


def normalize(record: Measurement) -> dict:
    validate_domain(record)

    unit, multiplier, offset = UNITS[record.metric][record.unit]

    return {
        "normalized_value": (
            None
            if record.value is None
            else record.value * multiplier + offset
        ),
        "normalized_unit": unit,
    }