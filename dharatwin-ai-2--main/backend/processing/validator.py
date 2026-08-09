"""Non-destructive validation for normalized climate datasets."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from backend.processing.schema import CORE_FIELDS


@dataclass
class ValidationResult:
    """Validation findings kept separate from cleaning actions."""

    valid: bool
    total_rows: int
    invalid_rows: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "valid": self.valid,
            "total_rows": self.total_rows,
            "invalid_rows": self.invalid_rows,
            "warnings": self.warnings,
            "errors": self.errors,
        }


def validate_dataset(dataframe: pd.DataFrame) -> ValidationResult:
    """Inspect raw/normalized data without mutating or deleting rows."""
    result = ValidationResult(valid=True, total_rows=len(dataframe))
    if dataframe.empty:
        result.valid = False
        result.errors.append("Dataset is empty.")
        return result

    if "timestamp" not in dataframe.columns:
        result.valid = False
        result.errors.append("Required timestamp column is missing.")
        return result

    invalid_timestamp = pd.to_datetime(dataframe["timestamp"], errors="coerce").isna()
    invalid_mask = invalid_timestamp.copy()
    if invalid_timestamp.any():
        result.warnings.append(f"Invalid or missing timestamps: {int(invalid_timestamp.sum())}.")

    coordinate_columns = {"latitude", "longitude"}.intersection(dataframe.columns)
    if coordinate_columns and coordinate_columns != set(CORE_FIELDS[1:]):
        result.valid = False
        result.errors.append("Latitude and longitude must be supplied together.")
    elif not coordinate_columns:
        result.warnings.append("Coordinates are unavailable; location cannot yet be geospatially resolved.")
    else:
        latitude = pd.to_numeric(dataframe["latitude"], errors="coerce")
        longitude = pd.to_numeric(dataframe["longitude"], errors="coerce")
        invalid_geo = latitude.isna() | longitude.isna() | ~latitude.between(-90, 90) | ~longitude.between(-180, 180)
        invalid_mask |= invalid_geo
        if invalid_geo.any():
            result.warnings.append(f"Missing or invalid coordinates: {int(invalid_geo.sum())}.")

    if "rainfall" in dataframe.columns:
        rainfall = pd.to_numeric(dataframe["rainfall"], errors="coerce")
        negative_rainfall = rainfall.notna() & (rainfall < 0)
        invalid_mask |= negative_rainfall
        if negative_rainfall.any():
            result.warnings.append(f"Negative rainfall values: {int(negative_rainfall.sum())}.")

    duplicates = dataframe.duplicated().sum()
    if duplicates:
        result.warnings.append(f"Duplicate rows: {int(duplicates)}.")
    result.invalid_rows = int(invalid_mask.sum())
    return result
