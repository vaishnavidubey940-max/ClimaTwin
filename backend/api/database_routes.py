"""Read-only observed-data APIs backed by the Phase 4 repository layer."""

from __future__ import annotations

from datetime import datetime

from flask import Blueprint, current_app, jsonify, request

from backend.config import PROJECT_ROOT
from backend.database.db import get_connection
from backend.database.repository import ClimateRepository
from backend.database.schema import initialize_schema


database_bp = Blueprint("database", __name__)


def _repository() -> tuple[ClimateRepository, object]:
    connection = get_connection(current_app.config["DATABASE_URL"], PROJECT_ROOT)
    initialize_schema(connection)
    return ClimateRepository(connection), connection


def _positive_int(value: str | None, name: str, default: int | None = None, maximum: int = 500) -> int | None:
    if value is None:
        return default
    try:
        parsed = int(value)
    except ValueError as error:
        raise ValueError(f"{name} must be an integer.") from error
    if not 1 <= parsed <= maximum:
        raise ValueError(f"{name} must be between 1 and {maximum}.")
    return parsed


def _coordinate(value: str | None, name: str, lower: float, upper: float) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except ValueError as error:
        raise ValueError(f"{name} must be numeric.") from error
    if not lower <= parsed <= upper:
        raise ValueError(f"{name} is outside its valid range.")
    return parsed


def _date(value: str | None, name: str) -> str | None:
    if value is None:
        return None
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{name} must be ISO 8601.") from error
    return value


@database_bp.get("/api/database/status")
def database_status():
    repository, connection = _repository()
    try:
        return jsonify(repository.database_status())
    finally:
        connection.close()


@database_bp.get("/api/locations")
def locations():
    try:
        limit = _positive_int(request.args.get("limit"), "limit", default=100)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    repository, connection = _repository()
    try:
        return jsonify({"data_type": "observed", "locations": repository.get_locations(limit=limit)})
    finally:
        connection.close()


@database_bp.get("/api/observations/latest")
def latest_observation():
    try:
        location_id = _positive_int(request.args.get("location_id"), "location_id")
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    repository, connection = _repository()
    try:
        observation = repository.get_latest_observation(location_id)
        if observation is None:
            return jsonify({"data_type": "observed", "observation": None}), 404
        return jsonify(observation)
    finally:
        connection.close()


@database_bp.get("/api/observations/history")
def observation_history():
    try:
        location_id = _positive_int(request.args.get("location_id"), "location_id")
        latitude = _coordinate(request.args.get("lat"), "lat", -90, 90)
        longitude = _coordinate(request.args.get("lon"), "lon", -180, 180)
        if (latitude is None) != (longitude is None):
            raise ValueError("lat and lon must be supplied together.")
        if location_id is None and latitude is None:
            raise ValueError("Provide location_id or both lat and lon.")
        start = _date(request.args.get("start"), "start")
        end = _date(request.args.get("end"), "end")
        limit = _positive_int(request.args.get("limit"), "limit", default=100)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    repository, connection = _repository()
    try:
        observations = repository.get_observation_history(
            location_id=location_id, latitude=latitude, longitude=longitude, start=start, end=end, limit=limit
        )
        return jsonify({"data_type": "observed", "observations": observations, "count": len(observations)})
    finally:
        connection.close()
