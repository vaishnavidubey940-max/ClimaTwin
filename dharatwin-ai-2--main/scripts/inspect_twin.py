from pathlib import Path
import sys
root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path: sys.path.insert(0, str(root))
from backend.config import Config, PROJECT_ROOT
from backend.database.db import get_connection
from backend.database.repository import ClimateRepository
from backend.database.schema import initialize_schema
from backend.digital_twin.twin_engine import TwinEngine

connection = get_connection(Config.DATABASE_URL, PROJECT_ROOT)
try:
    initialize_schema(connection)
    print(TwinEngine(ClimateRepository(connection), Config.DATA_MODE).get_all_twin_statuses())
finally: connection.close()
