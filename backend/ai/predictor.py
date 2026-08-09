"""Prediction service that validates features against saved model metadata."""

from __future__ import annotations

from datetime import datetime, timezone
import pandas as pd

from backend.ai.model_manager import ModelManager


def predict(target: str, features: dict, models_dir) -> dict:
    model, metadata = ModelManager(models_dir).load(target)
    missing = [name for name in metadata["features"] if name not in features or features[name] is None]
    if missing: raise ValueError("Missing required model features: " + ", ".join(missing))
    value = float(model.predict(pd.DataFrame([[features[name] for name in metadata["features"]]], columns=metadata["features"]))[0])
    return {"data_type": "ai_prediction", "target": target, "prediction": value, "unit": "C" if target == "temperature" else "input unit not declared", "prediction_for": features.get("prediction_for"), "generated_at": datetime.now(timezone.utc).isoformat(), "model": {"name": metadata["model"], "version": metadata["model_version"]}}
