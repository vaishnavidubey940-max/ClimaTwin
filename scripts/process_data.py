"""Process an approved local climate dataset into Phase 3 artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import Config
from backend.processing.processing_pipeline import ClimateProcessingPipeline, ProcessingError


def main() -> int:
    parser = argparse.ArgumentParser(description="Process a local climate CSV, JSON, or GeoJSON file.")
    parser.add_argument("--file", required=True, help="Path under data/raw.")
    parser.add_argument("--source", required=True, choices=["LOCAL", "MOSDAC", "IMD"], type=str.upper)
    args = parser.parse_args()
    pipeline = ClimateProcessingPipeline(Config.RAW_DATA_DIR, Config.PROCESSED_DATA_DIR, Config.REPORTS_DATA_DIR)
    try:
        result = pipeline.process_file(args.file, args.source)
    except ProcessingError as error:
        print(f"Processing failed: {error}", file=sys.stderr)
        return 1
    report = result["report"]
    print("File loaded")
    print(f"Rows detected: {report['total_rows']}")
    print(f"Rows retained: {report['valid_rows']}")
    print(f"Output location: {result['output_path']}")
    print(f"Report location: {result['report_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
