"""Phase 11 guarantees: provider slots are safe, inactive, and local-first."""

from backend.app import create_app
from backend.data_sources.imd_client import IMDClient
from backend.data_sources.mosdac_client import MOSDACClient


def test_provider_slots_are_not_configured_without_complete_environment():
    for client_type in (MOSDACClient, IMDClient):
        client = client_type({})
        assert client.status() == {"configured": False, "status": "NOT_CONFIGURED"}
        assert client.configured is False


def test_provider_slots_never_make_requests_when_disabled():
    for client_type in (MOSDACClient, IMDClient):
        client = client_type({})
        for method in (client.authenticate, client.fetch_latest_data, client.fetch_historical_data):
            try:
                method()
            except (NotImplementedError, RuntimeError):
                pass
            else:
                raise AssertionError("inactive provider slot unexpectedly performed work")


def test_status_endpoints_report_local_mode_and_safe_provider_states():
    app = create_app()
    app.config.update(TESTING=True, DATA_MODE="LOCAL")
    client = app.test_client()

    data_response = client.get("/api/data/status")
    system_response = client.get("/api/system/status")

    assert data_response.status_code == 200
    data_body = data_response.get_json()
    assert data_body["data_mode"] == "LOCAL"
    assert data_body["sources"]["mosdac"]["status"] == "NOT_CONFIGURED"
    assert data_body["sources"]["imd"]["status"] == "NOT_CONFIGURED"
    assert data_body["sources"]["local"]["status"] == "ready"

    assert system_response.status_code == 200
    system_body = system_response.get_json()
    assert system_body["data_mode"] == "LOCAL"
    assert system_body["mosdac"] == "NOT_CONFIGURED"
    assert system_body["imd"] == "NOT_CONFIGURED"

