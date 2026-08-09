"""Phase 7 service tests with explicit TEST DATA generated in a temporary database."""

from pathlib import Path
import pandas as pd

from backend.database.db import get_connection
from backend.database.importer import ProcessedDataImporter
from backend.ai.dataset_builder import observations_dataframe
from backend.ai.feature_engineering import build_target_dataset
from backend.ai.trainer import train_target
from backend.prediction.prediction_service import PredictionService


def _setup(tmp_path: Path):
    url = "sqlite:///" + (tmp_path / "prediction.db").as_posix(); connection = get_connection(url, tmp_path)
    rows = []
    for i, timestamp in enumerate(pd.date_range("2026-01-01", periods=40)):
        rows.append({"timestamp": timestamp.isoformat(), "latitude": 22.7, "longitude": 75.8, "temperature": 20 + i * .1, "rainfall": float(i % 5), "humidity": 60 + i % 3, "source": "LOCAL", "station_id": "TEST_DATA"})
    csv = tmp_path / "processed.csv"; pd.DataFrame(rows).to_csv(csv, index=False); ProcessedDataImporter(connection).import_csv(csv)
    frame = observations_dataframe(connection); models = tmp_path / "models"
    for target in ("temperature", "rainfall"):
        dataset, features = build_target_dataset(frame, target); train_target(dataset, features, target, models, tmp_path / "reports")
    return connection, models


def test_prediction_service_builds_and_persists_both_targets(tmp_path: Path):
    connection, models = _setup(tmp_path)
    try:
        result = PredictionService(connection, models).predict_location(1)
        assert set(result["predictions"]) == {"temperature", "rainfall"}
        assert all(value["data_type"] == "ai_prediction" for value in result["predictions"].values())
        assert len(connection.execute("SELECT * FROM predictions").fetchall()) == 2
        again = PredictionService(connection, models).predict_location(1)
        assert len(connection.execute("SELECT * FROM predictions").fetchall()) == 2
        assert again["predictions"]["temperature"]["prediction_horizon"]
    finally: connection.close()
