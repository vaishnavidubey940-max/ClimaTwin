"""Structured scenario input/state models."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ScenarioInput:
    location_id: int
    changes: dict[str, float]


@dataclass
class ScenarioState:
    scenario_id: str
    location_id: int
    baseline: dict[str, Any]
    changes: dict[str, float]
    scenario: dict[str, Any]
    comparison: dict[str, Any]
    model_assisted: dict[str, Any]
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {"data_type": "experimental_scenario", "scenario_id": self.scenario_id, "location_id": self.location_id, "baseline": self.baseline, "changes": self.changes, "scenario": self.scenario, "comparison": self.comparison, "model_assisted": self.model_assisted, "generated_at": self.generated_at, "disclaimer": "Experimental AI scenario — not an official weather or climate forecast."}
