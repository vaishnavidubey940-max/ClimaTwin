"""Snapshot serialization boundary."""

from backend.digital_twin.climate_state import ClimateState


def serialize(state: ClimateState) -> dict: return state.to_dict()
