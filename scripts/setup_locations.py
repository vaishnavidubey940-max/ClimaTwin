"""Setup the 5 required city locations and seed historical data for each."""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import Config
from backend.database.db import get_connection
from backend.database.schema import initialize_schema


CITIES = [
    {"name": "Indore",  "state": "Madhya Pradesh",  "district": "Indore",  "latitude": 22.7196, "longitude": 75.8577},
    {"name": "Gwalior", "state": "Madhya Pradesh",  "district": "Gwalior", "latitude": 26.2183, "longitude": 78.1828},
    {"name": "Delhi",   "state": "Delhi",            "district": "Delhi",   "latitude": 28.6139, "longitude": 77.2090},
    {"name": "Jhansi",  "state": "Uttar Pradesh",    "district": "Jhansi",  "latitude": 25.4484, "longitude": 78.5685},
    {"name": "Bhopal",  "state": "Madhya Pradesh",   "district": "Bhopal",  "latitude": 23.2599, "longitude": 77.4126},
]


def ensure_locations(connection):
    """Create or update the 5 city locations. Returns list of (location_id, city_dict)."""
    initialize_schema(connection)
    location_map = []

    for city in CITIES:
        # Check if a location with matching coordinates already exists (within 0.1 degree)
        row = connection.execute(
            "SELECT id, name FROM locations WHERE ABS(latitude - ?) < 0.1 AND ABS(longitude - ?) < 0.1 LIMIT 1",
            (city["latitude"], city["longitude"]),
        ).fetchone()

        if row:
            loc_id = int(row["id"])
            # Update name/state/district if they were NULL
            connection.execute(
                "UPDATE locations SET name=?, state=?, district=?, latitude=?, longitude=? WHERE id=?",
                (city["name"], city["state"], city["district"], city["latitude"], city["longitude"], loc_id),
            )
            print(f"  Updated existing location id={loc_id} -> {city['name']}")
        else:
            cursor = connection.execute(
                "INSERT INTO locations (name, state, district, latitude, longitude) VALUES (?, ?, ?, ?, ?)",
                (city["name"], city["state"], city["district"], city["latitude"], city["longitude"]),
            )
            loc_id = int(cursor.lastrowid)
            print(f"  Created new location id={loc_id} -> {city['name']}")

        location_map.append((loc_id, city))

    connection.commit()
    return location_map


def seed_city_data(connection, location_id, city, days=60):
    """Fetch and insert historical hourly data from Open-Meteo Archive API."""
    end_date = datetime.now(timezone.utc) - timedelta(days=5)
    start_date = end_date - timedelta(days=days)

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": city["latitude"],
        "longitude": city["longitude"],
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,surface_pressure,wind_speed_10m,cloud_cover",
    }

    print(f"  Fetching {days} days of data for {city['name']} (lat={city['latitude']}, lon={city['longitude']})...")
    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"  ERROR: Failed to fetch data for {city['name']}: {e}")
        return 0

    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    if not times:
        print(f"  WARNING: No hourly data received for {city['name']}.")
        return 0

    now_iso = datetime.now(timezone.utc).isoformat()
    inserted = 0

    for i, t in enumerate(times):
        ts = t + "Z" if not t.endswith("Z") else t
        temp = hourly["temperature_2m"][i]
        if temp is None:
            continue

        rain = hourly["precipitation"][i] or 0.0
        humidity = hourly["relative_humidity_2m"][i] or 50.0
        pressure = hourly["surface_pressure"][i] or 1013.25
        wind = hourly["wind_speed_10m"][i] or 0.0
        cloud = hourly["cloud_cover"][i] or 0.0
        obs_key = f"{location_id}-{ts}"

        try:
            cursor = connection.execute(
                """INSERT OR IGNORE INTO weather_observations
                   (location_id, timestamp, temperature, rainfall, humidity, pressure, wind_speed, cloud_cover, source, ingested_at, observation_key)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (location_id, ts, temp, rain, humidity, pressure, wind, cloud, "open-meteo-archive", now_iso, obs_key),
            )
            if cursor.rowcount == 1:
                inserted += 1
        except Exception as e:
            pass  # Skip duplicates silently

    connection.commit()
    return inserted


def main():
    print("=" * 60)
    print("DharaTwin AI — Multi-City Location Setup")
    print("=" * 60)

    connection = get_connection(Config.DATABASE_URL, PROJECT_ROOT)
    try:
        # Phase 1: Ensure all 5 locations exist
        print("\nPhase 1: Setting up locations...")
        location_map = ensure_locations(connection)

        # Phase 2: Seed historical data for each city
        print("\nPhase 2: Seeding historical data...")
        for loc_id, city in location_map:
            # Check how many observations already exist
            count = connection.execute(
                "SELECT COUNT(*) AS c FROM weather_observations WHERE location_id=?", (loc_id,)
            ).fetchone()["c"]

            if count >= 1000:
                print(f"  {city['name']} (id={loc_id}): Already has {count} observations. Skipping.")
                continue

            inserted = seed_city_data(connection, loc_id, city, days=60)
            total = connection.execute(
                "SELECT COUNT(*) AS c FROM weather_observations WHERE location_id=?", (loc_id,)
            ).fetchone()["c"]
            print(f"  {city['name']} (id={loc_id}): Inserted {inserted} new records. Total: {total}")

        # Phase 3: Final summary
        print("\n" + "=" * 60)
        print("FINAL STATUS")
        print("=" * 60)
        for loc_id, city in location_map:
            count = connection.execute(
                "SELECT COUNT(*) AS c FROM weather_observations WHERE location_id=?", (loc_id,)
            ).fetchone()["c"]
            status = "READY" if count >= 100 else "INSUFFICIENT_DATA"
            print(f"  {city['name']:12s} | id={loc_id} | observations={count:5d} | {status}")

    finally:
        connection.close()

    print("\nDone! All 5 cities are configured.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
