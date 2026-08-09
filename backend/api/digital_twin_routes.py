"""Digital Twin APIs with partial-state and invalid-location handling."""

from flask import Blueprint, current_app, jsonify, request

from backend.config import PROJECT_ROOT
from backend.database.db import get_connection
from backend.database.repository import ClimateRepository
from backend.database.schema import initialize_schema
from backend.digital_twin.twin_engine import TwinEngine


twin_bp = Blueprint("twin", __name__)


def _engine():
    connection = get_connection(current_app.config["DATABASE_URL"], PROJECT_ROOT); initialize_schema(connection)
    return TwinEngine(ClimateRepository(connection), current_app.config["DATA_MODE"]), connection


def _id(raw):
    try:
        value = int(raw)
        if value < 1: raise ValueError
        return value
    except (ValueError, TypeError): raise ValueError("location_id must be a positive integer.")


@twin_bp.get("/api/twin/<location_id>")
def get_twin(location_id):
    try: location_id = _id(location_id); engine, connection = _engine()
    except ValueError as error: return jsonify({"error": str(error)}), 400
    try: return jsonify(engine.get_twin(location_id))
    except ValueError as error: return jsonify({"error": str(error)}), 404
    finally: connection.close()


@twin_bp.get("/api/twin/<location_id>/status")
def twin_status(location_id):
    try: location_id = _id(location_id); engine, connection = _engine()
    except ValueError as error: return jsonify({"error": str(error)}), 400
    try:
        twin = engine.get_twin(location_id); return jsonify({"twin_id": twin["twin_id"], "quality": twin["quality"], "freshness": twin["data_status"]["freshness"], "data_mode": twin["data_status"]["mode"]})
    except ValueError as error: return jsonify({"error": str(error)}), 404
    finally: connection.close()


@twin_bp.post("/api/twin/<location_id>/update")
def update_twin(location_id):
    try: location_id = _id(location_id); engine, connection = _engine()
    except ValueError as error: return jsonify({"error": str(error)}), 400
    try: return jsonify(engine.update_twin(location_id))
    except ValueError as error: return jsonify({"error": str(error)}), 404
    finally: connection.close()


@twin_bp.get("/api/twins")
def all_twins():
    engine, connection = _engine()
    try: return jsonify({"twins": engine.get_all_twin_statuses(), "data_mode": current_app.config["DATA_MODE"]})
    finally: connection.close()
