"""Baseline versus scenario arithmetic comparisons."""


def compare(baseline: dict, scenario: dict, changes: dict) -> dict:
    fields = {}
    for field in ("temperature", "rainfall", "humidity"):
        if field in baseline and field in scenario:
            fields[field] = {"baseline": baseline[field], "scenario": scenario[field], "difference": scenario[field] - baseline[field], "provenance": "user_modified"}
    return fields
