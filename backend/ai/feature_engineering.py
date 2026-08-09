"""Time-series features built strictly from information available at time t."""

from __future__ import annotations

import pandas as pd


BASE_VARIABLES = ("temperature", "rainfall", "humidity", "pressure", "wind_speed", "cloud_cover")


def add_time_series_features(dataframe: pd.DataFrame) -> pd.DataFrame:
    result = dataframe.copy()
    result["timestamp"] = pd.to_datetime(result["timestamp"], errors="coerce")
    result = result.dropna(subset=["timestamp"]).sort_values(["location_id", "timestamp"], kind="stable")
    result["month"] = result["timestamp"].dt.month
    result["day_of_year"] = result["timestamp"].dt.dayofyear
    result["hour"] = result["timestamp"].dt.hour
    grouped = result.groupby("location_id", dropna=False, sort=False)
    for variable in BASE_VARIABLES:
        if variable not in result.columns:
            continue
        result[variable] = pd.to_numeric(result[variable], errors="coerce")
        result[f"{variable}_lag_1"] = grouped[variable].shift(1)
        result[f"{variable}_lag_2"] = grouped[variable].shift(2)
        result[f"{variable}_rolling_mean_3"] = grouped[variable].transform(lambda series: series.shift(1).rolling(3, min_periods=1).mean())
    return result


def build_target_dataset(observations: pd.DataFrame, target: str, horizon: int = 1) -> tuple[pd.DataFrame, list[str]]:
    if target not in {"temperature", "rainfall"}:
        raise ValueError("Target must be temperature or rainfall.")
    features = add_time_series_features(observations)
    grouped = features.groupby("location_id", dropna=False, sort=False)
    features["target"] = grouped[target].shift(-horizon)
    candidate = ["month", "day_of_year", "hour", "latitude", "longitude"]
    candidate += [column for column in features.columns if "_lag_" in column or "_rolling_mean_" in column]
    candidate += [variable for variable in BASE_VARIABLES if variable in features.columns and variable != target]
    feature_columns = [column for column in candidate if column in features.columns and features[column].notna().any()]
    dataset = features.dropna(subset=["target"] + feature_columns).copy()
    return dataset, feature_columns
