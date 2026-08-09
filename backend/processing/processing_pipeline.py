"""Reusable local climate-file processing pipeline, independent of Flask."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import pandas as pd

from backend.processing.cleaner import clean_dataset
from backend.processing.schema import map_schema
from backend.processing.validator import validate_dataset


class ProcessingError(ValueError):
    """Raised for a rejected input file or a dataset that cannot be processed."""


class ClimateProcessingPipeline:
    """Turn approved local raw files into standardized CSV and JSON audit reports."""

    allowed_sources = {"LOCAL", "MOSDAC", "IMD"}

    def __init__(self, raw_data_dir: str | Path, processed_data_dir: str | Path, reports_dir: str | Path):
        self.raw_data_dir = Path(raw_data_dir).resolve()
        self.processed_data_dir = Path(processed_data_dir)
        self.reports_dir = Path(reports_dir)

    def process_file(self, file_path: str | Path, source: str) -> dict[str, Any]:
        """Process an approved local file and write its derived artifacts."""
        normalized_source = source.upper()
        if normalized_source not in self.allowed_sources:
            raise ProcessingError("Source must be LOCAL, MOSDAC, or IMD.")
        path = self._approved_file(file_path)
        raw_dataframe = self._load_dataframe(path)
        mapping = map_schema(raw_dataframe)
        initial_validation = validate_dataset(mapping.dataframe)
        if initial_validation.errors:
            raise ProcessingError("; ".join(initial_validation.errors))

        cleaned, audit, units, unit_warnings = clean_dataset(mapping.dataframe)
        if cleaned.empty:
            raise ProcessingError("No valid rows remain after cleaning; no output was written.")

        processed_at = datetime.now(timezone.utc)
        cleaned["source"] = normalized_source
        cleaned["original_filename"] = path.name
        cleaned["ingested_at"] = processed_at.isoformat()
        cleaned["processed_at"] = processed_at.isoformat()
        final_validation = validate_dataset(cleaned)

        self.processed_data_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        artifact_id = processed_at.strftime("%Y%m%dT%H%M%S%fZ")
        output_name = f"processed_climate_{artifact_id}.csv"
        report_name = f"processing_report_{artifact_id}.json"
        output_path = self.processed_data_dir / output_name
        report_path = self.reports_dir / report_name
        cleaned.to_csv(output_path, index=False)

        warnings = initial_validation.warnings + unit_warnings
        if mapping.unmapped_columns:
            warnings.append("Unmapped columns retained without semantic interpretation: " + ", ".join(mapping.unmapped_columns))
        if mapping.ambiguous_columns:
            warnings.append("Ambiguous columns were not mapped: " + json.dumps(mapping.ambiguous_columns, sort_keys=True))
        report = {
            "source": normalized_source,
            "input_filename": path.name,
            "output_filename": output_name,
            "processing_time": processed_at.isoformat(),
            "total_rows": len(raw_dataframe),
            "valid_rows": len(cleaned),
            "invalid_rows": audit.rows_received - audit.rows_retained,
            "cleaning_audit": audit.as_dict(),
            "schema_mapping": mapping.report(),
            "unit_metadata": units,
            "warnings": warnings,
            "errors": final_validation.errors,
            "final_validation": final_validation.as_dict(),
        }
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return {"output_path": output_path, "report_path": report_path, "report": report}

    def _approved_file(self, file_path: str | Path) -> Path:
        path = Path(file_path).resolve()
        try:
            path.relative_to(self.raw_data_dir)
        except ValueError as error:
            raise ProcessingError("Input file must be located under the configured raw-data directory.") from error
        if not path.is_file():
            raise ProcessingError("Input file was not found.")
        if path.suffix.lower() not in {".csv", ".json", ".geojson"}:
            raise ProcessingError("Only CSV, JSON, and GeoJSON files are supported.")
        return path

    @staticmethod
    def _load_dataframe(path: Path) -> pd.DataFrame:
        if path.suffix.lower() == ".csv":
            try:
                return pd.read_csv(path)
            except pd.errors.EmptyDataError:
                return pd.DataFrame()
        content = json.loads(path.read_text(encoding="utf-8"))
        if path.suffix.lower() == ".geojson" or (
            isinstance(content, dict) and content.get("type") == "FeatureCollection"
        ):
            rows = []
            for feature in content.get("features", []):
                row = dict(feature.get("properties") or {})
                geometry = feature.get("geometry") or {}
                if geometry.get("type") == "Point" and len(geometry.get("coordinates", [])) >= 2:
                    row["longitude"], row["latitude"] = geometry["coordinates"][:2]
                rows.append(row)
            return pd.DataFrame(rows)
        if isinstance(content, list):
            return pd.DataFrame(content)
        if isinstance(content, dict) and isinstance(content.get("records"), list):
            return pd.DataFrame(content["records"])
        raise ProcessingError("JSON must contain a list, a 'records' list, or GeoJSON features.")
