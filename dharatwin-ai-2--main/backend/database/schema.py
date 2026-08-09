"""Idempotent SQLite schema for observed climate data and future empty tables."""

from __future__ import annotations

import sqlite3


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS locations (
    id INTEGER PRIMARY KEY,
    name TEXT,
    state TEXT,
    district TEXT,
    latitude REAL,
    longitude REAL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS weather_observations (
    id INTEGER PRIMARY KEY,
    location_id INTEGER REFERENCES locations(id),
    timestamp TEXT NOT NULL,
    temperature REAL,
    min_temperature REAL,
    max_temperature REAL,
    rainfall REAL,
    humidity REAL,
    pressure REAL,
    wind_speed REAL,
    cloud_cover REAL,
    source TEXT NOT NULL,
    source_dataset TEXT,
    original_file TEXT,
    station_id TEXT,
    ingested_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    observation_key TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS data_ingestion_logs (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL,
    filename TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT NOT NULL,
    rows_received INTEGER NOT NULL DEFAULT 0,
    rows_inserted INTEGER NOT NULL DEFAULT 0,
    rows_skipped INTEGER NOT NULL DEFAULT 0,
    rows_failed INTEGER NOT NULL DEFAULT 0,
    processing_report TEXT,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY,
    location_id INTEGER REFERENCES locations(id),
    prediction_for TEXT NOT NULL,
    generated_at TEXT NOT NULL,
    target TEXT NOT NULL,
    predicted_value REAL NOT NULL,
    unit TEXT,
    model_name TEXT,
    model_version TEXT,
    prediction_horizon TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scenario_runs (
    id INTEGER PRIMARY KEY,
    scenario_id TEXT,
    location_id INTEGER REFERENCES locations(id),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    baseline_json TEXT,
    changes_json TEXT,
    result_json TEXT,
    model_version TEXT,
    scenario_type TEXT
);

CREATE TABLE IF NOT EXISTS digital_twin_snapshots (
    id INTEGER PRIMARY KEY,
    location_id INTEGER NOT NULL REFERENCES locations(id),
    generated_at TEXT NOT NULL,
    observation_time TEXT,
    snapshot_json TEXT NOT NULL,
    data_mode TEXT NOT NULL,
    quality_status TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_observations_timestamp ON weather_observations(timestamp);
CREATE INDEX IF NOT EXISTS idx_observations_location ON weather_observations(location_id);
CREATE INDEX IF NOT EXISTS idx_observations_source ON weather_observations(source);
CREATE INDEX IF NOT EXISTS idx_ingestion_logs_completed ON data_ingestion_logs(completed_at);
"""


def initialize_schema(connection: sqlite3.Connection) -> None:
    """Create tables and indexes without deleting existing data."""
    connection.executescript(SCHEMA_SQL)
    columns = {row["name"] for row in connection.execute("PRAGMA table_info(predictions)").fetchall()}
    if "prediction_horizon" not in columns:
        connection.execute("ALTER TABLE predictions ADD COLUMN prediction_horizon TEXT")
    connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_predictions_identity ON predictions(location_id, target, prediction_for, model_version)")
    scenario_columns = {row["name"] for row in connection.execute("PRAGMA table_info(scenario_runs)").fetchall()}
    if "scenario_id" not in scenario_columns: connection.execute("ALTER TABLE scenario_runs ADD COLUMN scenario_id TEXT")
    if "scenario_type" not in scenario_columns: connection.execute("ALTER TABLE scenario_runs ADD COLUMN scenario_type TEXT")
    connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_scenario_id ON scenario_runs(scenario_id)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_twin_snapshots_location ON digital_twin_snapshots(location_id, generated_at)")
    connection.commit()
