"""SQLite connection helpers isolated from Flask and route code."""

from __future__ import annotations

import sqlite3
from pathlib import Path


def database_path(database_url: str, project_root: str | Path) -> Path:
    """Resolve the supported SQLite URL form without exposing it to API clients."""
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise ValueError("Phase 4 supports only sqlite:/// database URLs.")
    configured_path = Path(database_url.removeprefix(prefix))
    return configured_path if configured_path.is_absolute() else Path(project_root) / configured_path


def get_connection(database_url: str, project_root: str | Path) -> sqlite3.Connection:
    """Open a SQLite connection with safe row access and foreign keys enabled."""
    path = database_path(database_url, project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection
