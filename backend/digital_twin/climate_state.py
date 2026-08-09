"""Serializable state models with observed and AI-predicted values separated."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ClimateState:
    twin_id: str
    location: dict[str, Any]
    observed_state: dict[str, Any] | None
    predicted_state: dict[str, Any] | None
    historical_context: dict[str, Any]
    data_status: dict[str, Any]
    generated_at: str
    quality: dict[str, Any]

    def to_dict(self) -> dict[str, Any]: return asdict(self)
