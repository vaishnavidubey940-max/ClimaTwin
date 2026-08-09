"""Phase 7/8 API behavior with no trained models available."""

from backend.app import create_app


def test_prediction_and_twin_endpoints_fail_safely_without_fabricating_output(tmp_path):
    app = create_app(); app.config.update(TESTING=True, DATABASE_URL="sqlite:///" + (tmp_path / "api.db").as_posix(), MODELS_DIR=tmp_path / "models")
    client = app.test_client()
    assert client.post("/api/predict", json={"location_id": 1}).status_code in {400, 503}
    assert client.get("/api/predictions/status").status_code == 200
    assert client.get("/api/twin/999").status_code == 404
    assert client.get("/api/twin/not-an-id").status_code == 400
