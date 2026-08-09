"""Auditable dataset cleanup with no interpolation or silent replacement."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from backend.processing.geo_validator import coordinate_invalid_mask, normalize_coordinates
from backend.processing.normalizer import normalize_measurements
from backend.processing.temporal import normalize_timestamps


@dataclass
class CleaningAudit:
    rows_received: int
    blank_values_normalized: int = 0
    duplicate_rows_removed: int = 0
    invalid_timestamps_removed: int = 0
    invalid_coordinates_removed: int = 0
    negative_rainfall_removed: int = 0
    invalid_optional_numeric_values: int = 0
    rows_retained: int = 0

    def as_dict(self) -> dict[str, int]:
        return self.__dict__.copy()


def clean_dataset(dataframe: pd.DataFrame) -> tuple[pd.DataFrame, CleaningAudit, dict[str, str], list[str]]:
    """Clean only explicit invalidities and document every action."""
    result = dataframe.copy()
    audit = CleaningAudit(rows_received=len(result))
    blank_mask = result.astype("string").apply(lambda column: column.str.strip().eq("")).sum().sum()
    audit.blank_values_normalized = int(blank_mask)
    result = result.replace(r"^\s*$", pd.NA, regex=True)

    before_dedupe = len(result)
    result = result.drop_duplicates().copy()
    audit.duplicate_rows_removed = before_dedupe - len(result)

    result, invalid_timestamp_count = normalize_timestamps(result)
    timestamp_invalid = result["timestamp"].isna()
    audit.invalid_timestamps_removed = int(timestamp_invalid.sum())
    result = result.loc[~timestamp_invalid].copy()

    result = normalize_coordinates(result)
    invalid_geo = coordinate_invalid_mask(result)
    audit.invalid_coordinates_removed = int(invalid_geo.sum())
    result = result.loc[~invalid_geo].copy()

    result, units, unit_warnings = normalize_measurements(result)
    optional_invalid = 0
    for field in ("temperature", "min_temperature", "max_temperature", "humidity", "pressure", "wind_speed", "cloud_cover"):
        if field in result.columns:
            # Conversion failures become missing optional measurements, never fabricated values.
            optional_invalid += int(result[field].isna().sum())
    audit.invalid_optional_numeric_values = optional_invalid

    if "rainfall" in result.columns:
        negative_rainfall = result["rainfall"].notna() & (result["rainfall"] < 0)
        audit.negative_rainfall_removed = int(negative_rainfall.sum())
        result = result.loc[~negative_rainfall].copy()

    audit.rows_retained = len(result)
    return result, audit, units, unit_warnings
