"""What-If scenario APIs with explicit experimental labeling."""

from flask import Blueprint, current_app, jsonify, request

from backend.config import PROJECT_ROOT
from backend.database.db import get_connection
from backend.database.repository import ClimateRepository
from backend.database.schema import initialize_schema
from backend.digital_twin.twin_engine import TwinEngine
from backend.scenario.scenario_engine import ScenarioEngine


scenario_bp = Blueprint("scenarios", __name__)


def _engine():
    connection = get_connection(current_app.config["DATABASE_URL"], PROJECT_ROOT); initialize_schema(connection)
    repository = ClimateRepository(connection)
    return ScenarioEngine(TwinEngine(repository, current_app.config["DATA_MODE"]), repository, current_app.config), connection


@scenario_bp.post("/api/scenarios/run")
def run_scenario():
    body = request.get_json(silent=True) or {}
    try: location_id = int(body["location_id"]); changes = body["changes"]
    except (KeyError, TypeError, ValueError): return jsonify({"error": "location_id and changes are required."}), 400
    try:
        engine, connection = _engine()
        try: return jsonify(engine.run(location_id, changes))
        finally: connection.close()
    except ValueError as error: return jsonify({"error": str(error)}), 400


@scenario_bp.get("/api/scenarios/<scenario_id>")
def get_scenario(scenario_id):
    connection = get_connection(current_app.config["DATABASE_URL"], PROJECT_ROOT)
    try:
        initialize_schema(connection); result = ClimateRepository(connection).get_scenario(scenario_id)
        return jsonify(result) if result else (jsonify({"error": "Scenario not found."}), 404)
    finally: connection.close()


@scenario_bp.get("/api/scenarios/history")
def scenario_history():
    try: limit = min(max(int(request.args.get("limit", 50)), 1), 200); location_id = request.args.get("location_id"); location_id = int(location_id) if location_id is not None else None
    except ValueError: return jsonify({"error": "location_id and limit must be valid integers."}), 400
    connection = get_connection(current_app.config["DATABASE_URL"], PROJECT_ROOT)
    try: initialize_schema(connection); return jsonify({"data_type": "experimental_scenario", "scenarios": ClimateRepository(connection).scenario_history(location_id, limit)})
    finally: connection.close()
