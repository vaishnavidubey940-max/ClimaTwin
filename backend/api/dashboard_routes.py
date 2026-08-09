"""Unified dashboard/system status APIs."""

from flask import Blueprint, current_app, jsonify

from backend.config import PROJECT_ROOT
from backend.database.db import get_connection
from backend.database.repository import ClimateRepository
from backend.database.schema import initialize_schema
from backend.system.orchestrator import DharaTwinService


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/api/dashboard/<location_id>")
def dashboard_state(location_id):
    try: location_id = int(location_id)
    except ValueError: return jsonify({"error": "location_id must be an integer."}), 400
    connection = get_connection(current_app.config["DATABASE_URL"], PROJECT_ROOT)
    try: initialize_schema(connection); return jsonify(DharaTwinService(ClimateRepository(connection), current_app.config).dashboard(location_id))
    except ValueError as error: return jsonify({"error": str(error)}), 404
    finally: connection.close()


@dashboard_bp.get("/api/system/status")
def system_status():
    connection = get_connection(current_app.config["DATABASE_URL"], PROJECT_ROOT)
    try: initialize_schema(connection); return jsonify(DharaTwinService(ClimateRepository(connection), current_app.config).system_status())
    finally: connection.close()
