"""Coordinate validation without imposing an India-only geographic filter."""

from __future__ import annotations

import pandas as pd


def coordinate_invalid_mask(dataframe: pd.DataFrame) -> pd.Series:
    """Return invalid coordinate rows when a complete coordinate pair exists."""
    if not {"latitude", "longitude"}.issubset(dataframe.columns):
        return pd.Series(False, index=dataframe.index)
    latitude = pd.to_numeric(dataframe["latitude"], errors="coerce")
    longitude = pd.to_numeric(dataframe["longitude"], errors="coerce")
    return latitude.isna() | longitude.isna() | ~latitude.between(-90, 90) | ~longitude.between(-180, 180)


def normalize_coordinates(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Convert valid coordinate fields to numeric values; no spatial filtering occurs."""
    result = dataframe.copy()
    for field in ("latitude", "longitude"):
        if field in result.columns:
            result[field] = pd.to_numeric(result[field], errors="coerce")
    return result
