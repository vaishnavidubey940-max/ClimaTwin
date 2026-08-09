"""Build a unified state from stored observations and stored predictions."""

from __future__ import annotations

from datetime import datetime, timezone
import statistics

from backend.digital_twin.climate_state import ClimateState
from backend.digital_twin.freshness import freshness
from backend.digital_twin.quality import quality_status


class StateBuilder:
    def __init__(self, repository, data_mode: str): self.repository = repository; self.data_mode = data_mode

    def build(self, location_id: int) -> ClimateState:
        latest = self.repository.get_latest_observation(location_id)
        history = self.repository.get_observation_history(location_id=location_id, latitude=None, longitude=None, start=None, end=None, limit=100)
        predictions = self.repository.latest_predictions(location_id)
        location = (latest or {}).get("location") or next((x for x in self.repository.get_locations() if x["id"] == location_id), None)
        if location is None: raise ValueError("Location was not found.")
        observed = None if latest is None else {"data_type": "observed", "source": latest["source"], "timestamp": latest["timestamp"], "measurements": latest["measurements"]}
        pred_by_target = {row["target"]: row for row in predictions}; predicted = None
        if pred_by_target:
            predicted = {"data_type": "ai_prediction", "predictions": {target: {"prediction": row["predicted_value"], "unit": row["unit"], "prediction_for": row["prediction_for"], "model": row["model_name"], "model_version": row["model_version"], "prediction_horizon": row.get("prediction_horizon")} for target, row in pred_by_target.items()}}
        temps = [x["measurements"]["temperature"] for x in history if "temperature" in x["measurements"]]; rains = [x["measurements"]["rainfall"] for x in history if "rainfall" in x["measurements"]]
        historical = {"observation_count": len(history), "recent_average_temperature": statistics.mean(temps) if temps else None, "recent_rainfall_total": sum(rains) if rains else None}
        fresh = freshness(latest["timestamp"] if latest else None); quality = quality_status(observed, predicted, len(history), fresh)
        return ClimateState(twin_id=f"climatwin-location-{location_id}", location=location, observed_state=observed, predicted_state=predicted, historical_context=historical, data_status={"mode": self.data_mode, "freshness": fresh, "sources": sorted({x["source"] for x in history})}, generated_at=datetime.now(timezone.utc).isoformat(), quality=quality)
