"""Flask application entry point for ClimaTwin-IN."""

from __future__ import annotations

import logging

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from backend.api.data_status_routes import data_status_bp
from backend.api.database_routes import database_bp
from backend.api.ai_routes import ai_bp
from backend.api.health_routes import health_bp
from backend.api.map_routes import map_bp
from backend.api.digital_twin_routes import twin_bp
from backend.api.scenario_routes import scenario_bp
from backend.api.dashboard_routes import dashboard_bp
from backend.api.processed_status_routes import processed_status_bp
from backend.config import Config


def create_app() -> Flask:
    """Create and configure the Flask application."""
    Config.validate()

    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    app.register_blueprint(health_bp)
    app.register_blueprint(data_status_bp)
    app.register_blueprint(database_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(processed_status_bp)
    app.register_blueprint(map_bp)
    app.register_blueprint(twin_bp)
    app.register_blueprint(scenario_bp)
    app.register_blueprint(dashboard_bp)

    @app.get("/")
    def dashboard():
        return send_from_directory(Config.PROJECT_ROOT / "frontend", "index.html")

    @app.get("/frontend/<path:filename>")
    def frontend_assets(filename: str):
        return send_from_directory(Config.PROJECT_ROOT / "frontend", filename)

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(Exception)
    def unhandled_error(error: Exception):
        app.logger.exception("Unhandled application error")
        return jsonify({"error": "Internal server error"}), 500

    return app


app = create_app()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=True)
