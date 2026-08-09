"""Coordinates source adapters while keeping source selection replaceable."""

from __future__ import annotations

from typing import Any, Mapping

from backend.data_sources.imd_client import IMDClient
from backend.data_sources.local_loader import LocalDataLoader
from backend.data_sources.mosdac_client import MOSDACClient


class DataManager:
    """Provide source state without coupling routes to individual adapters."""

    def __init__(self, config: Mapping[str, Any]):
        self.data_mode = str(config["DATA_MODE"]).upper()
        self.mosdac = MOSDACClient(config)
        self.imd = IMDClient(config)
        self.local = LocalDataLoader(config["RAW_DATA_DIR"])

    def status(self) -> dict[str, Any]:
        """Return safe data-source readiness suitable for the dashboard/API."""
        return {
            "data_mode": self.data_mode,
            "sources": {
                "mosdac": self.mosdac.status(),
                "imd": self.imd.status(),
                "local": self.local.status(),
            },
        }

