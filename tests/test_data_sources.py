"""Phase 2 tests for inactive external clients and LOCAL-mode data status."""

from pathlib import Path

from backend.app import create_app
from backend.data_sources.imd_client import IMDClient
from backend.data_sources.local_loader import LocalDataLoader
from backend.data_sources.mosdac_client import MOSDACClient


def test_unconfigured_external_clients_wait_for_configuration():
    empty_config = {}

    expected = {
        "configured": False,
        "status": "NOT_CONFIGURED",
    }
    assert MOSDACClient(empty_config).status() == expected
    assert IMDClient(empty_config).status() == expected


def test_local_loader_loads_only_user_provided_csv(tmp_path: Path):
    source = tmp_path / "sample.csv"
    source.write_text("record,value\n1,25\n", encoding="utf-8")

    loader = LocalDataLoader(tmp_path)

    assert loader.status()["available"] is True
    assert loader.status()["file_count"] == 1
    assert loader.load(source).iloc[0]["value"] == 25


def test_data_status_endpoint_uses_local_mode_and_hides_credentials(tmp_path: Path):
    app = create_app()
    app.config.update(
        TESTING=True,
        DATA_MODE="LOCAL",
        RAW_DATA_DIR=tmp_path,
        MOSDAC_API_KEY="secret-should-not-appear",
        IMD_API_KEY="another-secret-should-not-appear",
    )

    response = app.test_client().get("/api/data/status")

    assert response.status_code == 200
    body = response.get_json()
    assert body["data_mode"] == "LOCAL"
    assert body["sources"]["local"]["status"] == "ready"
    assert "secret-should-not-appear" not in response.get_data(as_text=True)
    assert "another-secret-should-not-appear" not in response.get_data(as_text=True)
