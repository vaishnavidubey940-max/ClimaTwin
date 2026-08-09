"""Discovery and loading of developer-supplied local climate data files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


class LocalDataLoader:
    """Load CSV, JSON, and GeoJSON files without creating synthetic observations."""

    supported_extensions = {".csv", ".json", ".geojson"}

    def __init__(self, raw_data_dir: str | Path):
        self.raw_data_dir = Path(raw_data_dir)

    def status(self) -> dict[str, Any]:
        """Report local-data readiness, independently of whether files exist yet."""
        if not self.raw_data_dir.is_dir():
            return {"available": False, "status": "raw_data_directory_unavailable"}
        return {
            "available": True,
            "status": "ready",
            "file_count": len(self.list_files()),
        }

    def list_files(self) -> list[Path]:
        """List supported, user-provided files in the raw-data directory."""
        if not self.raw_data_dir.is_dir():
            return []
        return sorted(
            path
            for path in self.raw_data_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in self.supported_extensions
        )

    def load(self, file_path: str | Path) -> Any:
        """Load one supported local file; validation/normalization occurs in Phase 3."""
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Local data file was not found: {path}")
        if path.suffix.lower() not in self.supported_extensions:
            raise ValueError(f"Unsupported local data format: {path.suffix}")

        if path.suffix.lower() == ".csv":
            return pd.read_csv(path)
        with path.open("r", encoding="utf-8") as source_file:
            return json.load(source_file)

