"""Build inference features by reusing Phase 6 feature engineering."""

from __future__ import annotations

import pandas as pd

from backend.ai.feature_engineering import add_time_series_features


class PredictionInputBuilder:
    def __init__(self, connection):
        self.connection = connection

    def build(self, location_id: int, required_features: list[str]) -> tuple[dict, pd.Timestamp, int]:
        frame = pd.read_sql_query(
            "SELECT o.*, l.latitude, l.longitude FROM weather_observations o LEFT JOIN locations l ON l.id=o.location_id WHERE o.location_id=? ORDER BY o.timestamp",
            self.connection, params=(location_id,),
        )
        if frame.empty:
            raise ValueError("No observations are available for this location.")
        featured = add_time_series_features(frame)
        latest = featured.iloc[-1]
        missing = [name for name in required_features if name not in featured.columns or pd.isna(latest.get(name))]
        if missing:
            raise ValueError("Insufficient recent observations for required features: " + ", ".join(missing))
        return {name: float(latest[name]) for name in required_features}, pd.Timestamp(latest["timestamp"]), len(frame)
