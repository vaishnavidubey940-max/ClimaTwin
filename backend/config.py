"""Central application configuration loaded from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


class Config:
    """Base configuration for the Flask application."""

    PROJECT_ROOT = PROJECT_ROOT

    PROJECT_NAME = "ClimaTwin-IN"
    SECRET_KEY = os.getenv("SECRET_KEY", "development-only-change-me")
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "5000"))
    PILOT_STATE = os.getenv("PILOT_STATE", "Madhya Pradesh")
    DATA_MODE = os.getenv("DATA_MODE", "LOCAL").upper()
    RAW_DATA_DIR = PROJECT_ROOT / os.getenv("RAW_DATA_DIR", "data/raw")
    PROCESSED_DATA_DIR = PROJECT_ROOT / os.getenv(
        "PROCESSED_DATA_DIR", "data/processed"
    )
    REPORTS_DATA_DIR = PROJECT_ROOT / os.getenv("REPORTS_DATA_DIR", "data/reports")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/database/climatwin.db")
    MODELS_DIR = PROJECT_ROOT / os.getenv("MODELS_DIR", "models")
    ML_REPORTS_DIR = PROJECT_ROOT / os.getenv("ML_REPORTS_DIR", "reports/ml")
    SCENARIO_TEMPERATURE_MIN = float(os.getenv("SCENARIO_TEMPERATURE_MIN", "-5"))
    SCENARIO_TEMPERATURE_MAX = float(os.getenv("SCENARIO_TEMPERATURE_MAX", "5"))
    SCENARIO_RAINFALL_MIN = float(os.getenv("SCENARIO_RAINFALL_MIN", "-50"))
    SCENARIO_RAINFALL_MAX = float(os.getenv("SCENARIO_RAINFALL_MAX", "50"))
    SCENARIO_HUMIDITY_MIN = float(os.getenv("SCENARIO_HUMIDITY_MIN", "-30"))
    SCENARIO_HUMIDITY_MAX = float(os.getenv("SCENARIO_HUMIDITY_MAX", "30"))

    # TODO: Add official MOSDAC API configuration here.
    MOSDAC_API_URL = os.getenv("MOSDAC_API_URL", "")
    MOSDAC_API_KEY = os.getenv("MOSDAC_API_KEY", "")
    MOSDAC_USERNAME = os.getenv("MOSDAC_USERNAME", "")
    MOSDAC_PASSWORD = os.getenv("MOSDAC_PASSWORD", "")
    MOSDAC_DATASET_ID = os.getenv("MOSDAC_DATASET_ID", "")

    # TODO: Add official IMD API configuration here.
    IMD_API_URL = os.getenv("IMD_API_URL", "")
    IMD_API_KEY = os.getenv("IMD_API_KEY", "")
    IMD_USERNAME = os.getenv("IMD_USERNAME", "")
    IMD_PASSWORD = os.getenv("IMD_PASSWORD", "")
    IMD_DATASET_ID = os.getenv("IMD_DATASET_ID", "")

    # Optional map-provider slots. Leave blank to use the tokenless local-safe map style.
    MAP_STYLE_URL = os.getenv("MAP_STYLE_URL", "")
    MAP_PROVIDER_TOKEN = os.getenv("MAP_PROVIDER_TOKEN", "")
    MAP_SATELLITE_STYLE_URL = os.getenv("MAP_SATELLITE_STYLE_URL", "")
    MAP_TERRAIN_DEM_URL = os.getenv("MAP_TERRAIN_DEM_URL", "")
    GEOCODING_API_URL = os.getenv("GEOCODING_API_URL", "")
    GEOCODING_API_KEY = os.getenv("GEOCODING_API_KEY", "")

    @classmethod
    def validate(cls) -> None:
        """Fail early for invalid runtime configuration."""
        supported_modes = {"DEMO", "LOCAL", "LIVE"}
        if cls.DATA_MODE not in supported_modes:
            raise ValueError(
                f"DATA_MODE must be one of {sorted(supported_modes)}; got {cls.DATA_MODE!r}."
            )
