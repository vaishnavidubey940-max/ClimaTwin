"""Validation for model outputs before persistence."""

from __future__ import annotations

import math
from datetime import datetime


def validate_prediction(target: str, value: float, prediction_for: str, model_version: str) -> list[str]:
    if target not in {"temperature", "rainfall"}: raise ValueError("Unsupported prediction target.")
    if not math.isfinite(value): raise ValueError("Prediction is not a finite number.")
    datetime.fromisoformat(prediction_for.replace("Z", "+00:00"))
    if not model_version: raise ValueError("Model version is missing.")
    warnings = []
    if target == "rainfall" and value < 0: warnings.append("Rainfall model output was negative and was clipped to 0.0 mm.")
    return warnings
