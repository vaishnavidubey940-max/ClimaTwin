"""Tests for Phase 1 application health behavior."""

from backend.app import create_app


def test_health_endpoint_returns_application_status():
    app = create_app()
    app.config.update(TESTING=True)

    response = app.test_client().get("/api/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"
    assert response.get_json()["project"] == "ClimaTwin-IN"

