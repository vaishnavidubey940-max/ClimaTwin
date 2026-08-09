"""One read-only aggregation boundary for the final dashboard."""

from __future__ import annotations

import json
from pathlib import Path

from backend.ai.model_manager import ModelManager
from backend.digital_twin.twin_engine import TwinEngine


class DharaTwinService:
    def __init__(self, repository, config): self.repository = repository; self.config = config; self.twin = TwinEngine(repository, config)

    def dashboard(self, location_id: int) -> dict:
        twin = self.twin.get_twin(location_id); predictions = self.repository.latest_predictions(location_id)
        metrics = {}
        for target in ("temperature", "rainfall"):
            path = Path(self.config["ML_REPORTS_DIR"]) / f"{target}_training_report.json"
            metrics[target] = json.loads(path.read_text(encoding="utf-8")).get("metrics") if path.is_file() else None
        return {"location_id": location_id, "observed": twin.get("observed_state"), "predictions": predictions, "twin": twin, "historical_context": twin.get("historical_context"), "model_metrics": metrics, "data_mode": self.config["DATA_MODE"]}

    def system_status(self) -> dict:
        db = self.repository.database_status(); models = {target: (Path(self.config["MODELS_DIR"]) / target / "model.joblib").is_file() for target in ("temperature", "rainfall")}
        from backend.data_sources.data_manager import DataManager
        dm = DataManager(self.config)
        return {"backend": "READY", "database": db["status"].upper(), "data_mode": self.config["DATA_MODE"], "temperature_ai": "READY" if models["temperature"] else "NOT_AVAILABLE", "rainfall_ai": "READY" if models["rainfall"] else "NOT_AVAILABLE", "prediction_engine": "READY", "digital_twin": "READY", "scenario_engine": "READY", "mosdac": dm.mosdac.status()["status"], "imd": dm.imd.status()["status"]}
