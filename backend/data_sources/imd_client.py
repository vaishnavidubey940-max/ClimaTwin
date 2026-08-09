"""Open-Meteo client boundary (replacing IMD); fetches live weather data."""

from __future__ import annotations

from datetime import datetime, timezone
import requests
from typing import Any, Mapping

from backend.data_sources.base_client import BaseDataClient


class IMDClient(BaseDataClient):
    """Open-Meteo API integration (replaces IMD)."""

    source_name = "open-meteo"

    def __init__(self, config: Mapping[str, Any]):
        self._api_url = str(config.get("IMD_API_URL", "")).strip() or "https://api.open-meteo.com/v1/forecast"
        self._configured = bool(self._api_url)

    @property
    def configured(self) -> bool:
        return self._configured

    def status(self) -> dict[str, Any]:
        """Return a safe public status."""
        if not self.configured:
            return {
                "configured": False,
                "status": self.NOT_CONFIGURED,
            }
        return {"configured": True, "status": "ACTIVATED"}

    def authenticate(self) -> Any:
        pass

    def build_request(self, operation: str, **params: Any) -> dict[str, Any]:
        if not self.configured: raise RuntimeError("Open-Meteo is NOT_CONFIGURED.")
        return {"operation": operation, "params": params}

    def request_official_api(self, request_plan: dict[str, Any]) -> Any:
        params = request_plan["params"]
        query = {
            "latitude": params.get("latitude"),
            "longitude": params.get("longitude"),
            "current": "temperature_2m,relative_humidity_2m,precipitation,cloud_cover,surface_pressure,wind_speed_10m"
        }
        
        try:
            response = requests.get(self._api_url, params=query, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise RuntimeError(f"Open-Meteo API Error: {str(e)}")

    def parse_response(self, response: Any) -> Any:
        current = response.get("current", {})
        
        # Ensure timestamp is ISO format ending with Z or offset
        ts = current.get("time")
        if ts and not ts.endswith("Z") and "+" not in ts:
            ts += "Z" # Open-Meteo returns YYYY-MM-DDThh:mm without timezone, which defaults to UTC if timezone=GMT is not specified, wait let's just make it ISO.
            
        return {
            "timestamp": ts or datetime.now(timezone.utc).isoformat(),
            "measurements": {
                "temperature": current.get("temperature_2m"),
                "rainfall": current.get("precipitation", 0.0),
                "humidity": current.get("relative_humidity_2m"),
                "pressure": current.get("surface_pressure"),
                "wind_speed": current.get("wind_speed_10m"),
                "cloud_cover": current.get("cloud_cover")
            }
        }

    def fetch_latest_data(self, latitude: float | None = None, longitude: float | None = None) -> Any:
        """Fetch the latest weather for the given coordinates."""
        if not self.configured or latitude is None or longitude is None:
            return None
        
        plan = self.build_request("current", latitude=latitude, longitude=longitude)
        raw = self.request_official_api(plan)
        return self.parse_response(raw)

    def fetch_historical_data(self, **kwargs: Any) -> Any:
        return None
