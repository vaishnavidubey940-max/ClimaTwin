"""Map-ready observation API; values always originate in the local database."""

from flask import Blueprint, jsonify

from backend.api.database_routes import _repository


map_bp = Blueprint("map", __name__)


@map_bp.get("/api/map-data")
def map_data():
    repository, connection = _repository()
    try:
        return jsonify({"type": "FeatureCollection", "features": repository.get_map_features()})
    finally:
        connection.close()
