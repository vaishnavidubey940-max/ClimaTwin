"""Strict scenario input validation using configurable prototype UX bounds."""

from __future__ import annotations

import math


class ScenarioValidationError(ValueError): pass


class ScenarioValidator:
    def __init__(self, config):
        self.limits = {"temperature_delta": (config["SCENARIO_TEMPERATURE_MIN"], config["SCENARIO_TEMPERATURE_MAX"]), "rainfall_change_percent": (config["SCENARIO_RAINFALL_MIN"], config["SCENARIO_RAINFALL_MAX"]), "humidity_delta": (config["SCENARIO_HUMIDITY_MIN"], config["SCENARIO_HUMIDITY_MAX"])}

    def validate(self, location_id: int, changes: dict, baseline_measurements: dict) -> dict[str, float]:
        if not isinstance(location_id, int) or location_id < 1: raise ScenarioValidationError("location_id must be a positive integer.")
        if not isinstance(changes, dict): raise ScenarioValidationError("changes must be an object.")
        unknown = set(changes) - set(self.limits)
        if unknown: raise ScenarioValidationError("Unsupported scenario variables: " + ", ".join(sorted(unknown)))
        normalized = {}
        required = {"temperature_delta": "temperature", "rainfall_change_percent": "rainfall", "humidity_delta": "humidity"}
        for key, raw in changes.items():
            if isinstance(raw, bool): raise ScenarioValidationError(f"{key} must be numeric.")
            try: value = float(raw)
            except (TypeError, ValueError): raise ScenarioValidationError(f"{key} must be numeric.")
            if not math.isfinite(value): raise ScenarioValidationError(f"{key} must be finite.")
            low, high = self.limits[key]
            if not low <= value <= high: raise ScenarioValidationError(f"{key} must be between {low:g} and {high:g}; these are software/UX bounds, not scientific limits.")
            if required[key] not in baseline_measurements and value != 0: raise ScenarioValidationError(f"Baseline measurement '{required[key]}' is unavailable.")
            normalized[key] = value
        return normalized
