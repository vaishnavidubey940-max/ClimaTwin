"""Persistence adapter for prediction rows."""

from backend.database.repository import ClimateRepository


class PredictionRepository:
    def __init__(self, connection): self.repository = ClimateRepository(connection)
    def save(self, result: dict, location_id: int) -> bool:
        model = result["model"]
        return self.repository.insert_prediction(location_id=location_id, prediction_for=result["prediction_for"], generated_at=result["generated_at"], target=result["target"], predicted_value=result["prediction"], unit=result["unit"], model_name=model["name"], model_version=model["version"], prediction_horizon=result["prediction_horizon"])
