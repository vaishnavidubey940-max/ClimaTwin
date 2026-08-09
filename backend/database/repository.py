"""Repository methods for observed climate data; routes never issue raw SQL."""

from __future__ import annotations

import sqlite3
import json
from typing import Any


MEASUREMENT_FIELDS = (
    "temperature", "min_temperature", "max_temperature", "rainfall", "humidity",
    "pressure", "wind_speed", "cloud_cover",
)


class ClimateRepository:
    """Reusable, parameterized access to the Phase 4 SQLite database."""

    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def resolve_location(self, *, latitude: float | None, longitude: float | None, name: str | None = None,
                         state: str | None = None, district: str | None = None) -> int:
        """Find or create a location while preserving unavailable descriptive fields."""
        row = self.connection.execute(
            """SELECT id FROM locations WHERE latitude IS ? AND longitude IS ?
               AND name IS ? AND state IS ? AND district IS ? LIMIT 1""",
            (latitude, longitude, name, state, district),
        ).fetchone()
        if row:
            return int(row["id"])
        cursor = self.connection.execute(
            "INSERT INTO locations (name, state, district, latitude, longitude) VALUES (?, ?, ?, ?, ?)",
            (name, state, district, latitude, longitude),
        )
        return int(cursor.lastrowid)

    def insert_observation(self, observation: dict[str, Any]) -> bool:
        """Insert one observation; return False when its stable key already exists."""
        fields = ("location_id", "timestamp", *MEASUREMENT_FIELDS, "source", "source_dataset",
                  "original_file", "station_id", "ingested_at", "observation_key")
        placeholders = ", ".join("?" for _ in fields)
        cursor = self.connection.execute(
            f"INSERT OR IGNORE INTO weather_observations ({', '.join(fields)}) VALUES ({placeholders})",
            tuple(observation.get(field) for field in fields),
        )
        return cursor.rowcount == 1

    def create_ingestion_log(self, *, source: str, filename: str, started_at: str, rows_received: int,
                             processing_report: str | None) -> int:
        cursor = self.connection.execute(
            """INSERT INTO data_ingestion_logs
               (source, filename, started_at, status, rows_received, processing_report)
               VALUES (?, ?, ?, 'running', ?, ?)""",
            (source, filename, started_at, rows_received, processing_report),
        )
        return int(cursor.lastrowid)

    def finish_ingestion_log(self, log_id: int, *, status: str, completed_at: str, rows_inserted: int,
                             rows_skipped: int, rows_failed: int, error_message: str | None = None) -> None:
        self.connection.execute(
            """UPDATE data_ingestion_logs SET status = ?, completed_at = ?, rows_inserted = ?,
               rows_skipped = ?, rows_failed = ?, error_message = ? WHERE id = ?""",
            (status, completed_at, rows_inserted, rows_skipped, rows_failed, error_message, log_id),
        )

    def get_locations(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT id, name, state, district, latitude, longitude FROM locations ORDER BY id LIMIT ?", (limit,)
        ).fetchall()
        return [dict(row) for row in rows]

    def get_latest_observation(self, location_id: int | None = None) -> dict[str, Any] | None:
        query = """SELECT o.*, l.name AS location_name, l.state, l.district, l.latitude, l.longitude
                   FROM weather_observations o LEFT JOIN locations l ON l.id = o.location_id"""
        params: tuple[Any, ...] = ()
        if location_id is not None:
            query += " WHERE o.location_id = ?"
            params = (location_id,)
        row = self.connection.execute(query + " ORDER BY o.timestamp DESC, o.id DESC LIMIT 1", params).fetchone()
        return self._observation_payload(row) if row else None

    def get_observation_history(self, *, location_id: int | None, latitude: float | None, longitude: float | None,
                                start: str | None, end: str | None, limit: int) -> list[dict[str, Any]]:
        query = """SELECT o.*, l.name AS location_name, l.state, l.district, l.latitude, l.longitude
                   FROM weather_observations o LEFT JOIN locations l ON l.id = o.location_id WHERE 1 = 1"""
        params: list[Any] = []
        if location_id is not None:
            query += " AND o.location_id = ?"
            params.append(location_id)
        elif latitude is not None and longitude is not None:
            query += " AND l.latitude = ? AND l.longitude = ?"
            params.extend([latitude, longitude])
        if start:
            query += " AND o.timestamp >= ?"
            params.append(start)
        if end:
            query += " AND o.timestamp <= ?"
            params.append(end)
        query += " ORDER BY o.timestamp ASC, o.id ASC LIMIT ?"
        params.append(limit)
        return [self._observation_payload(row) for row in self.connection.execute(query, params).fetchall()]

    def database_status(self) -> dict[str, Any]:
        counts = self.connection.execute("SELECT COUNT(*) AS observations FROM weather_observations").fetchone()
        locations = self.connection.execute("SELECT COUNT(*) AS locations FROM locations").fetchone()
        last = self.connection.execute(
            "SELECT completed_at FROM data_ingestion_logs WHERE status = 'completed' ORDER BY completed_at DESC LIMIT 1"
        ).fetchone()
        return {
            "status": "ready", "database": "sqlite", "observations": counts["observations"],
            "locations": locations["locations"], "last_ingestion": last["completed_at"] if last else None,
        }

    def insert_prediction(self, *, location_id: int | None, prediction_for: str, generated_at: str, target: str,
                          predicted_value: float, unit: str, model_name: str, model_version: str,
                          prediction_horizon: str) -> bool:
        cursor = self.connection.execute(
            """INSERT OR IGNORE INTO predictions
               (location_id, prediction_for, generated_at, target, predicted_value, unit, model_name, model_version, prediction_horizon)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (location_id, prediction_for, generated_at, target, predicted_value, unit, model_name, model_version, prediction_horizon),
        )
        return cursor.rowcount == 1

    def latest_predictions(self, location_id: int | None = None) -> list[dict[str, Any]]:
        query = """SELECT p.*, l.name AS location_name, l.latitude, l.longitude
                   FROM predictions p LEFT JOIN locations l ON l.id = p.location_id"""
        params: tuple[Any, ...] = ()
        if location_id is not None:
            query += " WHERE p.location_id = ?"; params = (location_id,)
        rows = self.connection.execute(query + " ORDER BY p.prediction_for DESC, p.generated_at DESC", params).fetchall()
        return [dict(row) for row in rows]

    def prediction_history(self, location_id: int, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.connection.execute("SELECT * FROM predictions WHERE location_id = ? ORDER BY prediction_for DESC LIMIT ?", (location_id, limit)).fetchall()
        return [dict(row) for row in rows]

    def save_twin_snapshot(self, location_id: int, generated_at: str, observation_time: str | None, snapshot: dict, data_mode: str, quality_status: str) -> int:
        cursor = self.connection.execute("INSERT INTO digital_twin_snapshots (location_id, generated_at, observation_time, snapshot_json, data_mode, quality_status) VALUES (?, ?, ?, ?, ?, ?)", (location_id, generated_at, observation_time, json.dumps(snapshot), data_mode, quality_status))
        return int(cursor.lastrowid)

    def latest_twin_snapshot(self, location_id: int) -> dict[str, Any] | None:
        row = self.connection.execute("SELECT * FROM digital_twin_snapshots WHERE location_id=? ORDER BY generated_at DESC, id DESC LIMIT 1", (location_id,)).fetchone()
        if not row: return None
        output = dict(row); output["snapshot"] = json.loads(output.pop("snapshot_json")); return output

    def twin_locations(self) -> list[dict[str, Any]]:
        rows = self.connection.execute("SELECT id, name, state, district, latitude, longitude FROM locations ORDER BY id").fetchall()
        return [dict(row) for row in rows]

    def save_scenario(self, scenario: dict[str, Any]) -> None:
        self.connection.execute(
            """INSERT INTO scenario_runs (scenario_id, location_id, created_at, baseline_json, changes_json, result_json, model_version, scenario_type)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (scenario["scenario_id"], scenario["location_id"], scenario["generated_at"], json.dumps(scenario["baseline"]), json.dumps(scenario["changes"]), json.dumps(scenario), scenario.get("model_version"), scenario.get("scenario_type", "direct_user_modification")),
        )
        self.connection.commit()

    def get_scenario(self, scenario_id: str) -> dict[str, Any] | None:
        row = self.connection.execute("SELECT * FROM scenario_runs WHERE scenario_id=?", (scenario_id,)).fetchone()
        if not row: return None
        data = dict(row); return json.loads(data["result_json"])

    def scenario_history(self, location_id: int | None = None, limit: int = 50) -> list[dict[str, Any]]:
        query = "SELECT scenario_id, location_id, created_at, changes_json, scenario_type FROM scenario_runs"; params: list[Any] = []
        if location_id is not None: query += " WHERE location_id=?"; params.append(location_id)
        query += " ORDER BY created_at DESC LIMIT ?"; params.append(limit)
        rows = self.connection.execute(query, params).fetchall()
        output = []
        for row in rows:
            item = dict(row); item["changes"] = json.loads(item.pop("changes_json")); output.append(item)
        return output

    def get_map_features(self) -> list[dict[str, Any]]:
        """Return latest actual observation per mappable location for Leaflet."""
        rows = self.connection.execute(
            """SELECT o.*, l.name AS location_name, l.state, l.district, l.latitude, l.longitude
               FROM weather_observations o JOIN locations l ON l.id = o.location_id
               WHERE l.latitude IS NOT NULL AND l.longitude IS NOT NULL
                 AND o.id = (SELECT newest.id FROM weather_observations newest
                             WHERE newest.location_id = o.location_id
                             ORDER BY newest.timestamp DESC, newest.id DESC LIMIT 1)
               ORDER BY l.id"""
        ).fetchall()
        features = []
        for row in rows:
            is_test_data = bool(row["original_file"] and "TEST_DATA" in row["original_file"].upper())
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [row["longitude"], row["latitude"]]},
                "properties": {
                    "location_id": row["location_id"], "location_name": row["location_name"],
                    "timestamp": row["timestamp"], "temperature": row["temperature"],
                    "rainfall": row["rainfall"], "humidity": row["humidity"], "source": row["source"],
                    "data_type": "test_data" if is_test_data else "observed",
                    "original_file": row["original_file"],
                },
            })
        return features

    @staticmethod
    def _observation_payload(row: sqlite3.Row) -> dict[str, Any]:
        measurements = {field: row[field] for field in MEASUREMENT_FIELDS if row[field] is not None}
        return {
            "data_type": "observed", "source": row["source"], "timestamp": row["timestamp"],
            "location": {"id": row["location_id"], "name": row["location_name"], "state": row["state"],
                         "district": row["district"], "latitude": row["latitude"], "longitude": row["longitude"]},
            "measurements": measurements,
        }
