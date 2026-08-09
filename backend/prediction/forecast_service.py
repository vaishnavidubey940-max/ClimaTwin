"""Forecast facade; only the trained model's one-step horizon is exposed."""

from backend.prediction.prediction_service import PredictionService


class ForecastService:
    def __init__(self, prediction_service: PredictionService): self.prediction_service = prediction_service
    def generate(self, location_id: int) -> dict: return self.prediction_service.predict_location(location_id)
