"""Print an honest summary of observations available for ML training."""

from pathlib import Path
import sys
if str(Path(__file__).resolve().parent.parent) not in sys.path: sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.config import Config, PROJECT_ROOT
from backend.database.db import get_connection
from backend.ai.dataset_builder import inspect_dataset, observations_dataframe

connection = get_connection(Config.DATABASE_URL, PROJECT_ROOT)
try: print(inspect_dataset(observations_dataframe(connection)))
finally: connection.close()
