"""Timestamp normalization and transparent temporal metadata creation."""

from __future__ import annotations

import pandas as pd


def normalize_timestamps(dataframe: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Normalize parseable timestamps to ISO 8601 without inventing a timezone."""
    result = dataframe.copy()
    parsed = pd.to_datetime(result["timestamp"], errors="coerce", utc=False)
    invalid_count = int(parsed.isna().sum())
    result["timestamp"] = parsed.map(lambda value: value.isoformat() if pd.notna(value) else None)
    return result, invalid_count
