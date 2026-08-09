"""Train supported targets only when the real database has enough rows."""

from pathlib import Path
import sys
if str(Path(__file__).resolve().parent.parent) not in sys.path: sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.config import Config, PROJECT_ROOT
from backend.database.db import get_connection
from backend.ai.dataset_builder import observations_dataframe, InsufficientTrainingData
from backend.ai.feature_engineering import build_target_dataset
from backend.ai.trainer import train_target

connection = get_connection(Config.DATABASE_URL, PROJECT_ROOT)
try:
    frame = observations_dataframe(connection)
    for target in ("temperature", "rainfall"):
        try:
            dataset, features = build_target_dataset(frame, target); result = train_target(dataset, features, target, Config.MODELS_DIR, Config.ML_REPORTS_DIR); print(target, "trained", result["metrics"])
        except (InsufficientTrainingData, ValueError) as error: print(target, str(error))
finally: connection.close()
