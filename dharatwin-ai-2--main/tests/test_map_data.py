"""Phase 5 map API tests."""

from pathlib import Path
import pandas as pd

from backend.app import create_app
from backend.database.db import get_connection
from backend.database.importer import ProcessedDataImporter


def test_map_data_returns_observed_geojson(tmp_path: Path):
    url = "sqlite:///" + (tmp_path / "map.db").as_posix(); connection = get_connection(url, tmp_path)
    csv_path = tmp_path / "processed.csv"
    pd.DataFrame([{"timestamp": "2026-01-01T00:00:00", "latitude": 22.7, "longitude": 75.8, "temperature": 25, "source": "LOCAL"}]).to_csv(csv_path, index=False)
    ProcessedDataImporter(connection).import_csv(csv_path); connection.close()
    app = create_app(); app.config.update(TESTING=True, DATABASE_URL=url); response = app.test_client().get("/api/map-data")
    body = response.get_json(); assert response.status_code == 200 and body["type"] == "FeatureCollection"
    assert body["features"][0]["properties"]["data_type"] == "observed"
    assert body["features"][0]["geometry"]["coordinates"] == [75.8, 22.7]
