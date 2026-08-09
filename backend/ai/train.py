"""Train supported targets using the existing pipeline."""

from pathlib import Path
import sys

# Ensure backend can be resolved
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path: 
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import Config
from backend.database.db import get_connection
from backend.ai.dataset_builder import observations_dataframe, InsufficientTrainingData
from backend.ai.feature_engineering import build_target_dataset
from backend.ai.trainer import train_target

def main():
    connection = get_connection(Config.DATABASE_URL, PROJECT_ROOT)
    try:
        frame = observations_dataframe(connection)
        for target in ("temperature", "rainfall"):
            print(f"{target.title()}:")
            try:
                dataset, features = build_target_dataset(frame, target)
                result = train_target(dataset, features, target, Config.MODELS_DIR, Config.ML_REPORTS_DIR)
                print(f"  status: READY")
                print(f"  rows: {result['rows']['total']} (train: {result['rows']['train']}, val: {result['rows']['validation']}, test: {result['rows']['test']})")
                print(f"  MAE: {result['metrics']['mae']:.4f}")
                print(f"  RMSE: {result['metrics']['rmse']:.4f}")
                print(f"  R2: {result['metrics'].get('r2', 0.0):.4f}")
            except InsufficientTrainingData as error:
                print(f"  status: INSUFFICIENT TRAINING DATA")
                print(f"  error: {error}")
            except Exception as error:
                print(f"  status: ERROR")
                print(f"  error: {error}")
            print()
    finally:
        connection.close()

if __name__ == "__main__":
    main()
