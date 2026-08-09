"""Health-check endpoint for service monitoring and local verification."""

from flask import Blueprint, current_app, jsonify


health_bp = Blueprint("health", __name__)


@health_bp.get("/api/health")
def health_check():
    """Return the minimal service status without exposing secrets."""
    return jsonify(
        {
            "status": "ok",
            "project": current_app.config["PROJECT_NAME"],
            "data_mode": current_app.config["DATA_MODE"],
            "pilot_state": current_app.config["PILOT_STATE"],
        }
    )

