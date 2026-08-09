"""Central Phase 7 prediction service."""

from __future__ import annotations

from datetime import timedelta, timezone
from pathlib import Path
from datetime import datetime

import pandas as pd

from backend.ai.model_manager import ModelManager
from backend.database.schema import initialize_schema
from backend.prediction.input_builder import PredictionInputBuilder
from backend.prediction.prediction_repository import PredictionRepository
from backend.prediction.validator import validate_prediction


class PredictionService:
    def __init__(self, connection, models_dir: str | Path):
        initialize_schema(connection); self.connection = connection; self.models_dir = models_dir

    def predict_location(self, location_id: int, persist: bool = True) -> dict:
        predictions = {}; errors = {}
        for target in ("temperature", "rainfall"):
            try:
                model, metadata = ModelManager(self.models_dir).load(target)
                features, latest_time, observation_count = PredictionInputBuilder(self.connection).build(location_id, metadata["features"])
                value = float(model.predict(pd.DataFrame([features], columns=metadata["features"]))[0])
                # Phase 6 trains one-step-ahead models; preserve that exact horizon.
                prediction_time = latest_time + self._step(self.connection, location_id)
                prediction_for = prediction_time.isoformat()
                warnings = validate_prediction(target, value, prediction_for, metadata["model_version"])
                if target == "rainfall" and value < 0: value = 0.0
                result = {"data_type": "ai_prediction", "location_id": location_id, "target": target, "prediction": value, "unit": "C" if target == "temperature" else "input unit not declared", "prediction_for": prediction_for, "generated_at": datetime.now(timezone.utc).isoformat(), "prediction_horizon": metadata.get("horizon", "next observation (one chronological step)"), "observation_count": observation_count, "warnings": warnings, "model": {"name": metadata["model"], "version": metadata["model_version"]}}
                if persist: PredictionRepository(self.connection).save(result, location_id); self.connection.commit()
                predictions[target] = result
            except (FileNotFoundError, ValueError, KeyError) as error:
                errors[target] = str(error)
        if not predictions and errors:
            message = "; ".join(f"{key}: {value}" for key, value in errors.items())
            if all("No trained" in value or "model" in value.lower() for value in errors.values()):
                raise FileNotFoundError(message)
            raise ValueError(message)
        return {"data_type": "ai_prediction", "location_id": location_id, "predictions": predictions, "errors": errors}

    def _step(self, connection, location_id: int) -> pd.Timedelta:
        rows = pd.read_sql_query("SELECT timestamp FROM weather_observations WHERE location_id=? ORDER BY timestamp DESC LIMIT 3", connection, params=(location_id,))
        if len(rows) >= 2:
            times = pd.to_datetime(rows["timestamp"], errors="coerce").sort_values(); delta = times.diff().dropna().median()
            if pd.notna(delta) and delta > pd.Timedelta(0): return delta
        return pd.Timedelta(days=1)
