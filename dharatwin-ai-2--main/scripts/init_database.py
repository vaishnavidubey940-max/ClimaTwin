"""Idempotently create the local ClimaTwin-IN SQLite schema."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import Config, PROJECT_ROOT as CONFIG_PROJECT_ROOT
from backend.database.db import get_connection
from backend.database.schema import initialize_schema


def main() -> int:
    connection = get_connection(Config.DATABASE_URL, CONFIG_PROJECT_ROOT)
    try:
        initialize_schema(connection)
        print("Database initialized successfully.")
    finally:
        connection.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
