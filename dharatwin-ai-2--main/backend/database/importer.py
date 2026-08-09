"""Transactional importer for Phase 3 processed climate CSV artifacts."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Any

import pandas as pd

from backend.database.repository import ClimateRepository
from backend.database.schema import initialize_schema


class ProcessedDataImporter:
    """Import actual processed rows only; never generate measurements or predictions."""

    def __init__(self, connection):
        self.connection = connection

    def import_csv(self, file_path: str | Path, processing_report: str | None = None) -> dict[str, int]:
        path = Path(file_path)
        if not path.is_file() or path.suffix.lower() != ".csv":
            raise ValueError("A valid processed CSV file is required.")
        dataframe = pd.read_csv(path)
        required = {"timestamp", "source"}
        missing = required - set(dataframe.columns)
        if missing:
            raise ValueError("Processed CSV is missing required columns: " + ", ".join(sorted(missing)))
        initialize_schema(self.connection)
        rows = dataframe.where(pd.notna(dataframe), None).to_dict(orient="records")
        source = str(rows[0]["source"]) if rows else "LOCAL"
        now = datetime.now(timezone.utc).isoformat()
        repository = ClimateRepository(self.connection)
        self.connection.execute("BEGIN")
        log_id = repository.create_ingestion_log(source=source, filename=path.name, started_at=now,
                                                 rows_received=len(rows), processing_report=processing_report)
        inserted = skipped = failed = 0
        try:
            for row in rows:
                try:
                    location_id = repository.resolve_location(
                        latitude=self._number(row.get("latitude")), longitude=self._number(row.get("longitude")),
                        name=self._text(row.get("location_name")), state=self._text(row.get("state")),
                        district=self._text(row.get("district")),
                    )
                    observation = {
                        "location_id": location_id, "timestamp": self._text(row.get("timestamp")),
                        "source": self._text(row.get("source")), "source_dataset": self._text(row.get("source_dataset")),
                        "original_file": self._text(row.get("original_filename")), "station_id": self._text(row.get("station_id")),
                        "ingested_at": self._text(row.get("ingested_at")),
                    }
                    for field in ("temperature", "min_temperature", "max_temperature", "rainfall", "humidity", "pressure", "wind_speed", "cloud_cover"):
                        observation[field] = self._number(row.get(field))
                    observation["observation_key"] = self._observation_key(observation, row)
                    if repository.insert_observation(observation):
                        inserted += 1
                    else:
                        skipped += 1
                except (TypeError, ValueError):
                    failed += 1
            repository.finish_ingestion_log(log_id, status="completed", completed_at=datetime.now(timezone.utc).isoformat(),
                                            rows_inserted=inserted, rows_skipped=skipped, rows_failed=failed)
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
        return {"rows_received": len(rows), "rows_inserted": inserted, "rows_skipped": skipped, "rows_failed": failed}

    @staticmethod
    def _text(value: Any) -> str | None:
        return None if value is None or pd.isna(value) else str(value)

    @staticmethod
    def _number(value: Any) -> float | None:
        return None if value is None or value == "" or pd.isna(value) else float(value)

    @staticmethod
    def _observation_key(observation: dict[str, Any], row: dict[str, Any]) -> str:
        location_identity = "|".join(str(observation.get(key) or "") for key in ("location_id", "station_id"))
        stable = "|".join([str(observation.get("source") or ""), str(observation.get("timestamp") or ""), location_identity])
        return hashlib.sha256(stable.encode("utf-8")).hexdigest()
