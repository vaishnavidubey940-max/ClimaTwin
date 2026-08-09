"""Phase 3 processing tests using explicitly labelled TEST DATA only."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from backend.processing.processing_pipeline import ClimateProcessingPipeline, ProcessingError
from backend.processing.schema import map_schema
from backend.processing.validator import validate_dataset


def _pipeline(tmp_path: Path) -> tuple[ClimateProcessingPipeline, Path]:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    return (
        ClimateProcessingPipeline(raw_dir, tmp_path / "processed", tmp_path / "reports"),
        raw_dir,
    )


def _write_test_csv(raw_dir: Path, content: str, name: str = "TEST_DATA_climate.csv") -> Path:
    path = raw_dir / name
    path.write_text(content, encoding="utf-8")
    return path


def test_schema_mapping_maps_safe_aliases_and_reports_unknown_columns():
    frame = pd.DataFrame({"Date": ["2026-01-01"], "Lat": [20.0], "Lon": [77.0], "Temp": [25], "note": ["TEST DATA"]})

    result = map_schema(frame)

    assert result.mapping == {"Date": "timestamp", "Lat": "latitude", "Lon": "longitude", "Temp": "temperature"}
    assert result.unmapped_columns == ["note"]


def test_validator_detects_invalid_coordinates_negative_rainfall_and_timestamp():
    frame = pd.DataFrame({"timestamp": ["not-a-date"], "latitude": [95], "longitude": [181], "rainfall": [-1]})

    result = validate_dataset(frame)

    assert result.invalid_rows == 1
    assert any("timestamps" in warning for warning in result.warnings)
    assert any("coordinates" in warning for warning in result.warnings)
    assert any("Negative rainfall" in warning for warning in result.warnings)


def test_pipeline_generates_processed_csv_and_audit_report(tmp_path: Path):
    pipeline, raw_dir = _pipeline(tmp_path)
    input_file = _write_test_csv(
        raw_dir,
        "Date,Lat,Lon,Rainfall_mm,Temp,station\n"
        "2026-01-01T10:00:00,22.71,75.86,3.5,24.0,TEST_DATA_STATION\n"
        "2026-01-01T10:00:00,22.71,75.86,3.5,24.0,TEST_DATA_STATION\n"
        "bad-date,22.71,75.86,2.0,not-a-number,TEST_DATA_STATION\n",
    )

    result = pipeline.process_file(input_file, "LOCAL")

    assert result["output_path"].is_file()
    assert result["report_path"].is_file()
    processed = pd.read_csv(result["output_path"])
    report = json.loads(result["report_path"].read_text(encoding="utf-8"))
    assert len(processed) == 1
    assert processed.iloc[0]["source"] == "LOCAL"
    assert report["cleaning_audit"]["duplicate_rows_removed"] == 1
    assert report["cleaning_audit"]["invalid_timestamps_removed"] == 1
    assert report["input_filename"] == "TEST_DATA_climate.csv"


def test_pipeline_rejects_missing_timestamp_empty_data_and_paths_outside_raw_directory(tmp_path: Path):
    pipeline, raw_dir = _pipeline(tmp_path)
    missing_timestamp = _write_test_csv(raw_dir, "Lat,Lon,Rainfall_mm\n22.71,75.86,1.0\n")
    empty = _write_test_csv(raw_dir, "", "TEST_DATA_empty.csv")
    outside_file = tmp_path / "TEST_DATA_outside.csv"
    outside_file.write_text("Date,Lat,Lon\n2026-01-01,22,77\n", encoding="utf-8")

    with pytest.raises(ProcessingError, match="timestamp"):
        pipeline.process_file(missing_timestamp, "LOCAL")
    with pytest.raises(ProcessingError, match="Dataset is empty"):
        pipeline.process_file(empty, "LOCAL")
    with pytest.raises(ProcessingError, match="configured raw-data directory"):
        pipeline.process_file(outside_file, "LOCAL")


def test_pipeline_handles_missing_optional_fields_and_removes_invalid_geo_and_rainfall(tmp_path: Path):
    pipeline, raw_dir = _pipeline(tmp_path)
    input_file = _write_test_csv(
        raw_dir,
        "Date,Lat,Lon,Rainfall_mm\n"
        "2026-01-01,22.71,75.86,1.0\n"
        "2026-01-02,99,75.86,1.0\n"
        "2026-01-03,22.71,75.86,-2.0\n",
    )

    result = pipeline.process_file(input_file, "LOCAL")

    report = result["report"]
    assert report["valid_rows"] == 1
    assert report["cleaning_audit"]["invalid_coordinates_removed"] == 1
    assert report["cleaning_audit"]["negative_rainfall_removed"] == 1
    assert "temperature" not in pd.read_csv(result["output_path"]).columns
