"""Generate one-step forecasts for all stored locations."""

from pathlib import Path
import sys
root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path: sys.path.insert(0, str(root))
from backend.config import Config, PROJECT_ROOT
from backend.database.db import get_connection
from backend.database.repository import ClimateRepository
from backend.prediction.prediction_service import PredictionService

connection = get_connection(Config.DATABASE_URL, PROJECT_ROOT)
try:
    service = PredictionService(connection, Config.MODELS_DIR)
    for location in ClimateRepository(connection).twin_locations():
        try: print(service.predict_location(location["id"]))
        except (ValueError, FileNotFoundError) as error: print({"location_id": location["id"], "error": str(error)})
finally: connection.close()
