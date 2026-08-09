"""Conservative numeric and unit handling for climate measurements."""

from __future__ import annotations

import pandas as pd

from backend.processing.schema import CLIMATE_FIELDS


def normalize_measurements(dataframe: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str], list[str]]:
    """Convert numeric representations; never convert units whose input units are unknown."""
    result = dataframe.copy()
    units: dict[str, str] = {}
    warnings: list[str] = []
    for field in CLIMATE_FIELDS:
        if field not in result.columns:
            continue
        result[field] = pd.to_numeric(result[field], errors="coerce")
        units[field] = "input_unit_not_declared"
        warnings.append(f"Unit for '{field}' is not declared; value was preserved without conversion.")
    return result, units, warnings
