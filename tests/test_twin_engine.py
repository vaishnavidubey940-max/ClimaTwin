"""Phase 8 Digital Twin tests."""

from pathlib import Path
import pandas as pd

from backend.database.db import get_connection
from backend.database.importer import ProcessedDataImporter
from backend.database.repository import ClimateRepository
from backend.digital_twin.twin_engine import TwinEngine
from backend.digital_twin.freshness import freshness


def test_twin_keeps_observed_and_prediction_sections_separate(tmp_path: Path):
    connection = get_connection("sqlite:///" + (tmp_path / "twin.db").as_posix(), tmp_path)
    csv = tmp_path / "processed.csv"; pd.DataFrame([{"timestamp": "2026-01-01T00:00:00", "latitude": 22.7, "longitude": 75.8, "temperature": 25, "source": "LOCAL"}]).to_csv(csv, index=False); ProcessedDataImporter(connection).import_csv(csv)
    engine = TwinEngine(ClimateRepository(connection), "LOCAL"); state = engine.get_twin(1)
    assert state["twin_id"] == "climatwin-location-1" and state["observed_state"]["data_type"] == "observed"
    assert state["predicted_state"] is None and state["quality"]["status"] == "partial"
    snapshot = engine.update_twin(1); assert snapshot["data_status"]["mode"] == "LOCAL"
    assert connection.execute("SELECT COUNT(*) FROM digital_twin_snapshots").fetchone()[0] == 1
    connection.close()


def test_freshness_unknown_and_stale_are_explicit():
    assert freshness(None)["status"] == "UNKNOWN"
    assert freshness("2020-01-01T00:00:00Z")["status"] == "VERY_STALE"
