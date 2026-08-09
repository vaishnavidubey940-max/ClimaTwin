"""Apply only explicit user changes; no unsupported climate physics."""


def run_direct(measurements: dict, changes: dict) -> dict:
    result = dict(measurements)
    if "temperature_delta" in changes and "temperature" in measurements: result["temperature"] = measurements["temperature"] + changes["temperature_delta"]
    if "rainfall_change_percent" in changes and "rainfall" in measurements: result["rainfall"] = measurements["rainfall"] * (1 + changes["rainfall_change_percent"] / 100)
    if "humidity_delta" in changes and "humidity" in measurements: result["humidity"] = measurements["humidity"] + changes["humidity_delta"]
    return result
