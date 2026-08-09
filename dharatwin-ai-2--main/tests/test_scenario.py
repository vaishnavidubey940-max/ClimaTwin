"""Phase 9 What-If tests with explicit TEST DATA only."""

from pathlib import Path
import pandas as pd
import pytest

from backend.app import create_app
from backend.database.db import get_connection
from backend.database.importer import ProcessedDataImporter
from backend.database.repository import ClimateRepository
from backend.digital_twin.twin_engine import TwinEngine
from backend.scenario.scenario_engine import ScenarioEngine
from backend.scenario.validator import ScenarioValidationError


def _engine(tmp_path: Path):
    url = "sqlite:///" + (tmp_path / "scenario.db").as_posix(); connection = get_connection(url, tmp_path)
    csv = tmp_path / "processed.csv"; pd.DataFrame([{"timestamp": "2026-01-01T00:00:00", "latitude": 22.7, "longitude": 75.8, "temperature": 25, "rainfall": 10, "humidity": 60, "source": "LOCAL"}]).to_csv(csv, index=False); ProcessedDataImporter(connection).import_csv(csv)
    repo = ClimateRepository(connection); return connection, url, ScenarioEngine(TwinEngine(repo, "LOCAL"), repo, {"SCENARIO_TEMPERATURE_MIN": -5, "SCENARIO_TEMPERATURE_MAX": 5, "SCENARIO_RAINFALL_MIN": -50, "SCENARIO_RAINFALL_MAX": 50, "SCENARIO_HUMIDITY_MIN": -30, "SCENARIO_HUMIDITY_MAX": 30})


def test_direct_scenario_preserves_baseline_and_provenance(tmp_path: Path):
    connection, _, engine = _engine(tmp_path)
    result = engine.run(1, {"temperature_delta": 2, "rainfall_change_percent": 20})
    assert result["baseline"]["measurements"]["temperature"] == 25
    assert result["scenario"]["measurements"] == {"temperature": 27, "rainfall": 12, "humidity": 60}
    assert result["comparison"]["temperature"]["provenance"] == "user_modified"
    assert result["model_assisted"]["available"] is False
    assert connection.execute("SELECT COUNT(*) FROM scenario_runs").fetchone()[0] == 1
    connection.close()


def test_scenario_rejects_unsupported_and_out_of_range_changes(tmp_path: Path):
    connection, _, engine = _engine(tmp_path)
    with pytest.raises(ScenarioValidationError): engine.run(1, {"unknown": 1})
    with pytest.raises(ScenarioValidationError): engine.run(1, {"temperature_delta": 99})
    connection.close()


def test_scenario_api_run_retrieve_and_history(tmp_path: Path):
    connection, url, _ = _engine(tmp_path); connection.close()
    app = create_app(); app.config.update(TESTING=True, DATABASE_URL=url)
    client = app.test_client(); response = client.post("/api/scenarios/run", json={"location_id": 1, "changes": {"humidity_delta": 5}})
    assert response.status_code == 200; scenario_id = response.get_json()["scenario_id"]
    assert client.get("/api/scenarios/" + scenario_id).status_code == 200
    assert client.get("/api/scenarios/history?location_id=1").get_json()["scenarios"]
