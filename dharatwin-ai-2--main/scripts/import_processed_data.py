"""Import one approved Phase 3 processed CSV into SQLite."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import Config, PROJECT_ROOT as CONFIG_PROJECT_ROOT
from backend.database.db import get_connection
from backend.database.importer import ProcessedDataImporter


def main() -> int:
    parser = argparse.ArgumentParser(description="Import a processed ClimaTwin-IN CSV into SQLite.")
    parser.add_argument("--file", required=True, help="CSV file under data/processed.")
    args = parser.parse_args()
    path = Path(args.file).resolve()
    try:
        path.relative_to(Path(Config.PROCESSED_DATA_DIR).resolve())
    except ValueError:
        print("Import failed: input file must be under the configured processed-data directory.", file=sys.stderr)
        return 1
    connection = get_connection(Config.DATABASE_URL, CONFIG_PROJECT_ROOT)
    try:
        result = ProcessedDataImporter(connection).import_csv(path)
    except (ValueError, OSError) as error:
        print(f"Import failed: {error}", file=sys.stderr)
        return 1
    finally:
        connection.close()
    print("Database connected")
    print(f"Rows found: {result['rows_received']}")
    print(f"Rows inserted: {result['rows_inserted']}")
    print(f"Rows skipped: {result['rows_skipped']}")
    print(f"Rows failed: {result['rows_failed']}")
    print("Import completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
