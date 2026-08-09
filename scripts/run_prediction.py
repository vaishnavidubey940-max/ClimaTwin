"""Run and persist actual Phase 7 predictions for one location."""

from pathlib import Path
import argparse, sys
root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path: sys.path.insert(0, str(root))
from backend.config import Config, PROJECT_ROOT
from backend.database.db import get_connection
from backend.prediction.prediction_service import PredictionService

parser = argparse.ArgumentParser(); parser.add_argument("--location-id", type=int, required=True); args = parser.parse_args()
connection = get_connection(Config.DATABASE_URL, PROJECT_ROOT)
try: print(PredictionService(connection, Config.MODELS_DIR).predict_location(args.location_id))
finally: connection.close()
