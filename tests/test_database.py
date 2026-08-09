"""Phase 4 SQLite tests using only explicitly labelled TEST DATA."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from backend.app import create_app
from backend.database.db import get_connection
from backend.database.importer import ProcessedDataImporter
from backend.database.repository import ClimateRepository
from backend.database.schema import initialize_schema


def _database_url(path: Path) -> str:
    return "sqlite:///" + path.as_posix()


def _processed_csv(tmp_path: Path) -> Path:
    path = tmp_path / "processed_climate_TEST_DATA.csv"
    pd.DataFrame([{
        "timestamp": "2026-01-01T10:00:00", "latitude": 22.71, "longitude": 75.86,
        "temperature": 24.0, "rainfall": 3.5, "humidity": None, "source": "LOCAL",
        "station_id": "TEST_DATA_STATION", "original_filename": "TEST_DATA_source.csv",
        "ingested_at": "2026-01-01T10:05:00+00:00",
    }]).to_csv(path, index=False)
    return path


def test_schema_initialization_is_idempotent_and_creates_future_tables(tmp_path: Path):
    connection = get_connection(_database_url(tmp_path / "climatwin.db"), tmp_path)
    try:
        initialize_schema(connection)
        initialize_schema(connection)
        tables = {row["name"] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        assert {"locations", "weather_observations", "data_ingestion_logs", "predictions", "scenario_runs"} <= tables
    finally:
        connection.close()


def test_importer_inserts_observed_data_preserves_nulls_and_skips_duplicates(tmp_path: Path):
    connection = get_connection(_database_url(tmp_path / "climatwin.db"), tmp_path)
    try:
        importer = ProcessedDataImporter(connection)
        dataset = _processed_csv(tmp_path)
        first = importer.import_csv(dataset)
        second = importer.import_csv(dataset)
        repository = ClimateRepository(connection)
        latest = repository.get_latest_observation()
        log = connection.execute("SELECT rows_inserted, rows_skipped, status FROM data_ingestion_logs ORDER BY id DESC LIMIT 1").fetchone()
        assert first == {"rows_received": 1, "rows_inserted": 1, "rows_skipped": 0, "rows_failed": 0}
        assert second["rows_inserted"] == 0 and second["rows_skipped"] == 1
        assert latest["data_type"] == "observed"
        assert "humidity" not in latest["measurements"]
        assert log["status"] == "completed"
    finally:
        connection.close()


def test_repository_history_and_flask_read_only_apis(tmp_path: Path):
    database_file = tmp_path / "climatwin.db"
    database_url = _database_url(database_file)
    connection = get_connection(database_url, tmp_path)
    try:
        ProcessedDataImporter(connection).import_csv(_processed_csv(tmp_path))
    finally:
        connection.close()

    app = create_app()
    app.config.update(TESTING=True, DATABASE_URL=database_url)
    client = app.test_client()
    status = client.get("/api/database/status")
    locations = client.get("/api/locations")
    latest = client.get("/api/observations/latest")
    history = client.get("/api/observations/history?lat=22.71&lon=75.86&limit=10")
    invalid = client.get("/api/observations/history?lat=500&lon=75")

    assert status.status_code == 200 and status.get_json()["observations"] == 1
    assert locations.status_code == 200 and len(locations.get_json()["locations"]) == 1
    assert latest.status_code == 200 and latest.get_json()["data_type"] == "observed"
    assert history.status_code == 200 and history.get_json()["count"] == 1
    assert invalid.status_code == 400
