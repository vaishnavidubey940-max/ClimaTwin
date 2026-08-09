"""FastAPI backend for the DharaTwin dashboard.

This app reuses the existing repository, processing, prediction, twin, and
scenario services. Flask remains available for backwards compatibility; run
this module with Uvicorn when a native FastAPI server is preferred.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.ai.model_manager import ModelManager
from backend.config import Config, PROJECT_ROOT
from backend.data_sources.data_manager import DataManager
from backend.database.db import get_connection
from backend.database.repository import ClimateRepository
from backend.database.schema import initialize_schema
from backend.digital_twin.twin_engine import TwinEngine
from backend.prediction.prediction_service import PredictionService
from backend.scenario.scenario_engine import ScenarioEngine
from backend.system.orchestrator import DharaTwinService


Config.validate()
app = FastAPI(title="ClimaTwin-IN API", version="1.0.0", docs_url="/docs", redoc_url="/redoc")
app.add_middleware(CORSMiddleware, allow_origins=["http://127.0.0.1:3000", "http://localhost:3000", "http://127.0.0.1:5000", "http://localhost:5000"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


def repository() -> tuple[ClimateRepository, Any]:
    connection = get_connection(Config.DATABASE_URL, PROJECT_ROOT)
    initialize_schema(connection)
    return ClimateRepository(connection), connection


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "project": Config.PROJECT_NAME, "data_mode": Config.DATA_MODE, "pilot_state": Config.PILOT_STATE}


@app.get("/api/data/status")
def data_status() -> dict[str, Any]:
    return DataManager(vars(Config)).status()


@app.get("/api/database/status")
def database_status() -> dict[str, Any]:
    repo, connection = repository()
    try:
        return repo.database_status()
    finally:
        connection.close()


@app.get("/api/locations")
def locations(limit: int = Query(100, ge=1, le=500)) -> dict[str, Any]:
    repo, connection = repository()
    try:
        return {"data_type": "observed", "locations": repo.get_locations(limit=limit)}
    finally:
        connection.close()


@app.get("/api/observations/latest")
def latest_observation(location_id: int = Query(..., ge=1)) -> dict[str, Any]:
    repo, connection = repository()
    try:
        value = repo.get_latest_observation(location_id)
        if value is None:
            raise HTTPException(status_code=404, detail="Observation not found.")
        return value
    finally:
        connection.close()


@app.get("/api/observations/history")
def observation_history(location_id: int = Query(..., ge=1), start: str | None = None, end: str | None = None, limit: int = Query(100, ge=1, le=500)) -> dict[str, Any]:
    repo, connection = repository()
    try:
        values = repo.get_observation_history(location_id=location_id, latitude=None, longitude=None, start=start, end=end, limit=limit)
        return {"data_type": "observed", "observations": values, "count": len(values)}
    finally:
        connection.close()


@app.get("/api/map-data")
def map_data() -> dict[str, Any]:
    repo, connection = repository()
    try:
        return {"type": "FeatureCollection", "features": repo.get_map_features()}
    finally:
        connection.close()


@app.get("/api/model/metrics")
def model_metrics() -> dict[str, Any]:
    output: dict[str, Any] = {}
    for target in ("temperature", "rainfall"):
        report = Path(Config.ML_REPORTS_DIR) / f"{target}_training_report.json"
        if report.is_file():
            data = json.loads(report.read_text(encoding="utf-8"))
            output[target] = {"available": True, "model": data.get("model"), "metrics": data.get("metrics"), "rows": data.get("rows"), "periods": data.get("periods"), "features": data.get("features")}
        else:
            output[target] = {"available": False, "status": "model_unavailable"}
    return output


@app.get("/api/twin/{location_id}")
def twin(location_id: int) -> dict[str, Any]:
    repo, connection = repository()
    try:
        try:
            return TwinEngine(repo, vars(Config)).get_twin(location_id)
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
    finally:
        connection.close()


@app.post("/api/scenarios/run")
def run_scenario(body: dict[str, Any]) -> dict[str, Any]:
    try:
        location_id = int(body["location_id"])
        changes = body["changes"]
    except (KeyError, TypeError, ValueError) as error:
        raise HTTPException(status_code=400, detail="location_id and changes are required.") from error
    repo, connection = repository()
    try:
        return ScenarioEngine(TwinEngine(repo, vars(Config)), repo, vars(Config)).run(location_id, changes)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    finally:
        connection.close()


@app.get("/api/system/status")
def system_status() -> dict[str, Any]:
    repo, connection = repository()
    try:
        return DharaTwinService(repo, vars(Config)).system_status()
    finally:
        connection.close()


@app.get("/api/dashboard/{location_id}")
def dashboard(location_id: int) -> dict[str, Any]:
    repo, connection = repository()
    try:
        return DharaTwinService(repo, vars(Config)).dashboard(location_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    finally:
        connection.close()


@app.get("/api/ai/status")
def ai_status() -> dict[str, Any]:
    """Return trained-model health for each supported target."""
    from backend.ai.model_manager import ModelManager
    result = {}
    for target in ("temperature", "rainfall"):
        try:
            _, metadata = ModelManager(Config.MODELS_DIR).load(target)
            result[target] = {
                "status": "READY",
                "model_name": metadata.get("model", "RandomForestRegressor"),
                "model_version": metadata.get("model_version", "unknown"),
                "trained_at": metadata.get("model_version", "unknown"),
                "features": metadata.get("features", []),
                "metrics": metadata.get("metrics", {}),
                "rows": metadata.get("rows", {}),
            }
        except FileNotFoundError:
            result[target] = {"status": "NOT_AVAILABLE", "message": f"No trained {target} model is available."}
    return result


@app.post("/api/predict/temperature")
def predict_temperature(body: dict[str, Any]) -> dict[str, Any]:
    """Run temperature prediction for a location."""
    try:
        location_id = int(body.get("location_id", 0))
    except (TypeError, ValueError) as error:
        raise HTTPException(status_code=400, detail="location_id is required.") from error
    if location_id < 1:
        raise HTTPException(status_code=400, detail="location_id must be a positive integer.")
    repo, connection = repository()
    try:
        from backend.prediction.prediction_service import PredictionService
        service = PredictionService(connection, Config.MODELS_DIR)
        result = service.predict_location(location_id, persist=True)
        temp = result.get("predictions", {}).get("temperature")
        if temp is None:
            errors = result.get("errors", {})
            return {"success": False, "status": "PREDICTION_FAILED", "message": errors.get("temperature", "Temperature prediction unavailable.")}
        return {
            "success": True,
            "prediction": {"temperature": temp["prediction"], "unit": "°C", "prediction_for": temp.get("prediction_for")},
            "model": temp.get("model", {}),
            "timestamp": temp.get("generated_at"),
        }
    except FileNotFoundError as error:
        return {"success": False, "status": "MODEL_NOT_TRAINED", "message": str(error)}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    finally:
        connection.close()


@app.get("/api/predict/{location_id}")
def predict_location(location_id: int) -> dict[str, Any]:
    """Run all available predictions for a location."""
    repo, connection = repository()
    try:
        from backend.prediction.prediction_service import PredictionService
        return PredictionService(connection, Config.MODELS_DIR).predict_location(location_id, persist=True)
    except FileNotFoundError as error:
        return {"data_type": "ai_prediction", "location_id": location_id, "predictions": {}, "errors": {"temperature": str(error), "rainfall": str(error)}}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    finally:
        connection.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.fastapi_app:app", host="127.0.0.1", port=5000, reload=True)
