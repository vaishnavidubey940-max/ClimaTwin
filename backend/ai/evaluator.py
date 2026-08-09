"""Actual regression metrics and persistence baseline comparison."""

from __future__ import annotations

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def regression_metrics(actual, predicted, baseline=None) -> dict[str, float | None]:
    actual = np.asarray(actual); predicted = np.asarray(predicted)
    result = {"mae": float(mean_absolute_error(actual, predicted)), "rmse": float(np.sqrt(mean_squared_error(actual, predicted))), "r2": float(r2_score(actual, predicted)) if len(actual) > 1 else None}
    if baseline is not None:
        baseline = np.asarray(baseline); result["baseline_mae"] = float(mean_absolute_error(actual, baseline)); result["baseline_rmse"] = float(np.sqrt(mean_squared_error(actual, baseline)))
    return result
