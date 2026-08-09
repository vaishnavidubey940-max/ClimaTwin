"""Configurable freshness labels for LOCAL or future live data."""

from __future__ import annotations

from datetime import datetime, timezone


def freshness(timestamp: str | None, now: datetime | None = None, fresh_days: int = 2, stale_days: int = 30) -> dict[str, object]:
    if not timestamp: return {"status": "UNKNOWN", "age_hours": None}
    try: observed = datetime.fromisoformat(timestamp.replace("Z", "+00:00")); observed = observed.replace(tzinfo=timezone.utc) if observed.tzinfo is None else observed
    except ValueError: return {"status": "UNKNOWN", "age_hours": None}
    current = now or datetime.now(timezone.utc); age_hours = max(0.0, (current - observed).total_seconds() / 3600)
    status = "FRESH" if age_hours <= fresh_days * 24 else "STALE" if age_hours <= stale_days * 24 else "VERY_STALE"
    return {"status": status, "age_hours": round(age_hours, 2), "observed_at": timestamp}
