"""NASA CMR client boundary (replacing MOSDAC); fetches satellite metadata."""

from __future__ import annotations

import json
from datetime import datetime, timezone
import requests
from typing import Any, Mapping

from backend.data_sources.base_client import BaseDataClient


class MOSDACClient(BaseDataClient):
    """NASA Earthdata CMR API integration (replaces MOSDAC)."""

    source_name = "nasa-cmr"

    def __init__(self, config: Mapping[str, Any]):
        self._api_url = str(config.get("MOSDAC_API_URL", "")).strip() or "https://cmr.earthdata.nasa.gov/search/granules.json"
        self._api_key = str(config.get("MOSDAC_API_KEY", "")).strip()
        self._username = str(config.get("MOSDAC_USERNAME", "")).strip()
        self._password = str(config.get("MOSDAC_PASSWORD", "")).strip()
        self._dataset_id = str(config.get("MOSDAC_DATASET_ID", "")).strip() or "C1748058432-LPCLOUD"
        
        self._configured = bool(self._api_url and self._dataset_id)

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
        if not self.configured: raise RuntimeError("NASA CMR is NOT_CONFIGURED.")
        return {"operation": operation, "dataset_id": self._dataset_id, "params": params}

    def request_official_api(self, request_plan: dict[str, Any]) -> Any:
        params = request_plan["params"]
        query = {
            "collection_concept_id": request_plan["dataset_id"],
            "page_size": 1,
            "sort_key": "-start_date"
        }
        
        if params.get("latitude") is not None and params.get("longitude") is not None:
            query["point"] = f"{params['longitude']},{params['latitude']}"
            
        try:
            response = requests.get(self._api_url, params=query, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise RuntimeError(f"NASA CMR API Error: {str(e)}")

    def parse_response(self, response: Any) -> Any:
        entries = response.get("feed", {}).get("entry", [])
        if not entries:
            return None
        
        latest = entries[0]
        links = latest.get("links", [])
        data_link = next((link["href"] for link in links if link.get("rel") == "http://esipfed.org/ns/discovery/1.1/data#"), None)
        
        return {
            "granule_id": latest.get("id"),
            "title": latest.get("title"),
            "updated": latest.get("updated"),
            "time_start": latest.get("time_start"),
            "data_link": data_link,
            "source_dataset": "MOD11A1"
        }

    def fetch_latest_data(self, latitude: float | None = None, longitude: float | None = None) -> Any:
        """Fetch the latest granule metadata for the given coordinates."""
        if not self.configured:
            return None
        
        plan = self.build_request("search", latitude=latitude, longitude=longitude)
        raw = self.request_official_api(plan)
        return self.parse_response(raw)

    def fetch_historical_data(self, **kwargs: Any) -> Any:
        return None
