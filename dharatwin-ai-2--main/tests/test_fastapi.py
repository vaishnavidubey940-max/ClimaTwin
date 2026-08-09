from fastapi.testclient import TestClient

from backend.fastapi_app import app


client = TestClient(app)


def test_fastapi_health_and_local_status():
    health = client.get("/api/health")
    status = client.get("/api/data/status")
    assert health.status_code == 200
    assert health.json()["data_mode"] == "LOCAL"
    assert status.status_code == 200
    assert status.json()["sources"]["local"]["status"] == "ready"


def test_fastapi_map_and_system_status():
    assert client.get("/api/map-data").status_code == 200
    system = client.get("/api/system/status")
    assert system.status_code == 200
    assert system.json()["data_mode"] == "LOCAL"
