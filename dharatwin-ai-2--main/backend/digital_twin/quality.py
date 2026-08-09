"""Transparent quality status, not an invented scientific score."""


def quality_status(observed: dict | None, predicted: dict | None, historical_count: int, freshness: dict) -> dict:
    missing = [] if not observed else [field for field in ("temperature", "rainfall", "humidity") if field not in observed.get("measurements", {})]
    warnings = []
    if observed is None: warnings.append("No stored observation is available.")
    if predicted is None: warnings.append("No stored AI prediction is available.")
    if historical_count < 2: warnings.append("Historical context is limited.")
    if freshness.get("status") in {"STALE", "VERY_STALE"}: warnings.append("Observation is not fresh; DATA_MODE may be LOCAL.")
    status = "complete" if not warnings and not missing else "partial"
    return {"status": status, "missing_fields": missing, "warnings": warnings}
