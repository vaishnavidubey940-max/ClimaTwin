"""Experimental scenario coordinator built on the Digital Twin baseline."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from backend.scenario.comparison import compare
from backend.scenario.scenario import ScenarioState
from backend.scenario.scenario_runner import run_direct
from backend.scenario.validator import ScenarioValidator


class ScenarioEngine:
    def __init__(self, twin_engine, repository, config): self.twin_engine = twin_engine; self.repository = repository; self.validator = ScenarioValidator(config)

    def run(self, location_id: int, changes: dict, persist: bool = True) -> dict:
        twin = self.twin_engine.get_twin(location_id)
        observed = twin.get("observed_state")
        if not observed: raise ValueError("Scenario requires an existing observed baseline.")
        normalized = self.validator.validate(location_id, changes, observed["measurements"])
        scenario_values = run_direct(observed["measurements"], normalized)
        state = ScenarioState(str(uuid4()), location_id, observed, normalized, {"data_type": "experimental_scenario", "measurements": scenario_values, "provenance": "user_modified", "baseline_timestamp": observed.get("timestamp")}, compare(observed["measurements"], scenario_values, normalized), {"available": False, "reason": "No scenario-compatible model semantics are configured; values shown are direct user modifications."}, datetime.now(timezone.utc).isoformat())
        output = state.to_dict()
        if persist: self.repository.save_scenario(output)
        return output
