"""Fix timestamps in the database to have consistent ISO format with seconds."""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import Config
from backend.database.db import get_connection
import pandas as pd

conn = get_connection(Config.DATABASE_URL, PROJECT_ROOT)
cursor = conn.cursor()

# Read all timestamps
rows = cursor.execute("SELECT id, timestamp FROM weather_observations").fetchall()
fixed = 0
for row_id, ts in rows:
    if ts and "Z" in ts and ts.count(":") == 1:
        # Format like 2026-06-04T00:00Z -> 2026-06-04T00:00:00Z
        new_ts = ts.replace("Z", ":00Z")
        cursor.execute("UPDATE weather_observations SET timestamp=? WHERE id=?", (new_ts, row_id))
        fixed += 1

conn.commit()
print(f"Fixed {fixed} timestamps")

# Verify
df = pd.read_sql_query("SELECT timestamp FROM weather_observations", conn)
parsed = pd.to_datetime(df["timestamp"], errors="coerce")
print(f"Total: {len(df)}, Parsed OK: {parsed.notna().sum()}, Failed: {parsed.isna().sum()}")
conn.close()
