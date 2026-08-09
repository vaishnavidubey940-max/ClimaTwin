"""Safe summary of processed artifacts; no arbitrary filesystem access."""

from __future__ import annotations

import json
from pathlib import Path

from flask import Blueprint, current_app, jsonify


processed_status_bp = Blueprint("processed_status", __name__)


@processed_status_bp.get("/api/data/processed/status")
def processed_status():
    """Return available artifact counts and the latest processing report summary."""
    processed_dir = Path(current_app.config["PROCESSED_DATA_DIR"])
    reports_dir = Path(current_app.config["REPORTS_DATA_DIR"])
    processed_count = len(list(processed_dir.glob("processed_climate_*.csv"))) if processed_dir.is_dir() else 0
    reports = sorted(reports_dir.glob("processing_report_*.json")) if reports_dir.is_dir() else []
    latest = None
    if reports:
        latest_report = json.loads(reports[-1].read_text(encoding="utf-8"))
        latest = {
            "source": latest_report.get("source"),
            "processing_time": latest_report.get("processing_time"),
            "valid_rows": latest_report.get("valid_rows"),
        }
    return jsonify({"processed_datasets": processed_count, "latest_processing": latest})
