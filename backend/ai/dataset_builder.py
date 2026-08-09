"""Database-backed ML dataset inspection and sufficiency checks."""

from __future__ import annotations

import pandas as pd


class InsufficientTrainingData(ValueError):
    """Raised when a target cannot support a defensible chronological model."""


def observations_dataframe(connection) -> pd.DataFrame:
    return pd.read_sql_query("SELECT o.*, l.latitude, l.longitude FROM weather_observations o LEFT JOIN locations l ON l.id = o.location_id ORDER BY o.timestamp", connection)


def inspect_dataset(dataframe: pd.DataFrame) -> dict[str, object]:
    if dataframe.empty:
        return {"rows": 0, "date_start": None, "date_end": None, "columns": [], "missing_percent": {}}
    timestamps = pd.to_datetime(dataframe["timestamp"], errors="coerce")
    return {"rows": len(dataframe), "date_start": timestamps.min().isoformat() if timestamps.notna().any() else None, "date_end": timestamps.max().isoformat() if timestamps.notna().any() else None, "columns": list(dataframe.columns), "missing_percent": (dataframe.isna().mean() * 100).round(2).to_dict()}


def require_sufficient(dataset: pd.DataFrame, minimum: int = 20) -> None:
    if len(dataset) < minimum:
        raise InsufficientTrainingData(f"INSUFFICIENT TRAINING DATA: {len(dataset)} rows available; minimum is {minimum}.")
