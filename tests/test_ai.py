"""Phase 6 tests use generated TEST DATA only and never alter project observations."""

from pathlib import Path
import pandas as pd
import pytest

from backend.ai.dataset_builder import InsufficientTrainingData
from backend.ai.feature_engineering import add_time_series_features, build_target_dataset
from backend.ai.predictor import predict
from backend.ai.trainer import train_target


def test_features_are_shifted_and_rolling_values_do_not_use_current_or_future_rows():
    frame = pd.DataFrame({"location_id": [1, 1, 1, 1], "timestamp": pd.date_range("2026-01-01", periods=4), "temperature": [10, 20, 30, 40], "rainfall": [1, 2, 3, 4]})
    result = add_time_series_features(frame)
    assert pd.isna(result.iloc[0]["temperature_lag_1"])
    assert result.iloc[1]["temperature_lag_1"] == 10
    assert result.iloc[2]["temperature_rolling_mean_3"] == 15
    assert result.iloc[3]["temperature_rolling_mean_3"] == 20


def test_dataset_builder_and_training_are_chronological(tmp_path: Path):
    frame = pd.DataFrame({"location_id": [1] * 40, "latitude": [22.7] * 40, "longitude": [75.8] * 40, "timestamp": pd.date_range("2026-01-01", periods=40), "temperature": [20 + i * .1 for i in range(40)], "rainfall": [float(i % 5) for i in range(40)], "humidity": [60 + i % 3 for i in range(40)]})
    dataset, features = build_target_dataset(frame, "temperature")
    assert len(dataset) == 37 and "temperature_lag_1" in features
    metadata = train_target(dataset, features, "temperature", tmp_path / "models", tmp_path / "reports")
    assert metadata["rows"]["train"] < metadata["rows"]["test"] + metadata["rows"]["validation"] + metadata["rows"]["train"]
    assert (tmp_path / "models" / "temperature" / "model.joblib").is_file()
    prediction = predict("temperature", {feature: float(dataset.iloc[-1][feature]) for feature in features}, tmp_path / "models")
    assert prediction["data_type"] == "ai_prediction"


def test_insufficient_training_data_is_explicit(tmp_path: Path):
    frame = pd.DataFrame({"location_id": [1, 1], "timestamp": pd.date_range("2026-01-01", periods=2), "temperature": [20, 21]})
    dataset, features = build_target_dataset(frame, "temperature")
    with pytest.raises(InsufficientTrainingData, match="INSUFFICIENT TRAINING DATA"):
        train_target(dataset, features, "temperature", tmp_path / "models", tmp_path / "reports")
