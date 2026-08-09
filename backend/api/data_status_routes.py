"""Read-only endpoint exposing safe data-source readiness."""

from flask import Blueprint, current_app, jsonify

from backend.data_sources.data_manager import DataManager


data_status_bp = Blueprint("data_status", __name__)


@data_status_bp.get("/api/data/status")
def data_status():
    """Show source readiness without exposing provider credentials."""
    return jsonify(DataManager(current_app.config).status())
