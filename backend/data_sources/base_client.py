"""Common contract for data-source adapters.

Clients expose configuration state separately from retrieval. This lets the
application run safely before an official provider integration is enabled.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseDataClient(ABC):
    """Interface implemented by every external climate-data source client."""

    source_name: str
    NOT_CONFIGURED = "NOT_CONFIGURED"
    CONFIGURED_NOT_ACTIVATED = "CONFIGURED_NOT_ACTIVATED"

    @abstractmethod
    def status(self) -> dict[str, Any]:
        """Return non-sensitive readiness information for the source."""

    @abstractmethod
    def fetch_latest_data(self) -> Any:
        """Retrieve latest source data once official integration is enabled."""

    @abstractmethod
    def fetch_historical_data(self, **kwargs: Any) -> Any:
        """Retrieve historical source data once official integration is enabled."""

    @abstractmethod
    def authenticate(self) -> Any:
        """Reserved authentication hook; must be implemented with official docs later."""

    @abstractmethod
    def parse_response(self, response: Any) -> Any:
        """Reserved provider response mapping hook."""
