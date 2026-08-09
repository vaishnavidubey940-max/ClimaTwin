"""Prediction and model-metrics APIs; failures are reported without crashing Flask."""

from __future__ import annotations

import json
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request

from backend.ai.predictor import predict
from backend.config import PROJECT_ROOT
from backend.database.db import get_connection
from backend.database.repository import ClimateRepository
from backend.database.schema import initialize_schema
from backend.prediction.prediction_service import PredictionService


ai_bp = Blueprint("ai", __name__)


@ai_bp.post("/api/predict")
def prediction():
    body = request.get_json(silent=True) or {}
    if body.get("location_id") is not None and "target" not in body:
        try:
            location_id = int(body["location_id"])
            connection = get_connection(current_app.config["DATABASE_URL"], PROJECT_ROOT)
            try:
                result = PredictionService(connection, current_app.config["MODELS_DIR"]).predict_location(location_id)
                return jsonify(result)
            finally:
                connection.close()
        except FileNotFoundError as error:
            return jsonify({"error": str(error), "status": "model_unavailable"}), 503
        except (ValueError, TypeError) as error:
            return jsonify({"error": str(error)}), 400
    target = body.get("target")
    features = body.get("features") or {}
    if target not in {"temperature", "rainfall"} or not isinstance(features, dict):
        return jsonify({"error": "target must be temperature or rainfall and features must be an object."}), 400
    try:
        result = predict(target, features, current_app.config["MODELS_DIR"])
    except FileNotFoundError as error:
        return jsonify({"error": str(error), "status": "model_unavailable"}), 503
    except (ValueError, TypeError) as error:
        return jsonify({"error": str(error)}), 400
    location_id = body.get("location_id")
    if location_id is not None:
        try:
            location_id = int(location_id)
            connection = get_connection(current_app.config["DATABASE_URL"], PROJECT_ROOT); initialize_schema(connection)
            ClimateRepository(connection).insert_prediction(location_id=location_id, prediction_for=result["prediction_for"], generated_at=result["generated_at"], target=target, predicted_value=result["prediction"], unit=result["unit"], model_name=result["model"]["name"], model_version=result["model"]["version"], prediction_horizon=result.get("prediction_horizon", "manual feature inference"))
            connection.commit(); connection.close()
        except (ValueError, TypeError):
            return jsonify({"error": "location_id must be an integer."}), 400
    return jsonify(result)


@ai_bp.get("/api/predictions/latest")
def latest_predictions():
    location_id = request.args.get("location_id")
    try: location_id = int(location_id) if location_id is not None else None
    except ValueError: return jsonify({"error": "location_id must be an integer."}), 400
    connection = get_connection(current_app.config["DATABASE_URL"], PROJECT_ROOT)
    try:
        initialize_schema(connection); return jsonify({"data_type": "ai_prediction", "predictions": ClimateRepository(connection).latest_predictions(location_id)})
    finally: connection.close()


@ai_bp.get("/api/predictions/history")
def prediction_history():
    try:
        location_id = int(request.args["location_id"]); limit = min(max(int(request.args.get("limit", 100)), 1), 500)
    except (KeyError, ValueError): return jsonify({"error": "location_id and a valid limit are required."}), 400
    connection = get_connection(current_app.config["DATABASE_URL"], PROJECT_ROOT)
    try:
        initialize_schema(connection); return jsonify({"data_type": "ai_prediction", "predictions": ClimateRepository(connection).prediction_history(location_id, limit)})
    finally: connection.close()


@ai_bp.get("/api/predictions/status")
def prediction_status():
    connection = get_connection(current_app.config["DATABASE_URL"], PROJECT_ROOT)
    try:
        initialize_schema(connection); rows = ClimateRepository(connection).latest_predictions(); latest = max((row.get("generated_at") for row in rows if row.get("generated_at")), default=None)
    finally: connection.close()
    output = {"temperature": {"status": "READY" if (Path(current_app.config["MODELS_DIR"]) / "temperature" / "model.joblib").is_file() else "NOT_AVAILABLE"}, "rainfall": {"status": "READY" if (Path(current_app.config["MODELS_DIR"]) / "rainfall" / "model.joblib").is_file() else "NOT_AVAILABLE"}, "latest_prediction_time": latest}
    return jsonify(output)


@ai_bp.get("/api/model/metrics")
def model_metrics():
    report_dir = Path(current_app.config["ML_REPORTS_DIR"])
    output = {}
    for target in ("temperature", "rainfall"):
        report = report_dir / f"{target}_training_report.json"
        if report.is_file():
            data = json.loads(report.read_text(encoding="utf-8")); output[target] = {"available": True, "model": data.get("model"), "metrics": data.get("metrics"), "rows": data.get("rows"), "periods": data.get("periods"), "features": data.get("features")}
        else:
            output[target] = {"available": False, "status": "model_unavailable"}
    return jsonify(output)
